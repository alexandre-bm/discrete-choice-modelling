from dataclasses import dataclass,field
from pandas import DataFrame
import numpy as np
import pickle
from copy import deepcopy

import biogeme.models as models
import biogeme.biogeme as bio
from biogeme.expressions import Beta

from .utility_function import UtiliyFunction, ALT_NAME
from .database import Data

import os
DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PARENT_DIR = os.path.abspath(os.path.join(DIR, os.pardir))
WORKDIR = os.getcwd()


@dataclass
class Model:
    name: str
    data: Data
    F: UtiliyFunction
    nested: bool = False
    estimation: bool = True
    simulation_data: Data = field(init=False)
    coefficients: DataFrame = field(init=False)
    betas: dict = field(init=False)
    simulation: DataFrame = field(init=False)
    market_shares: DataFrame = field(init=False)
    rmse: float = field(init=False)

    def __post_init__(self):
        self.simulation_data = deepcopy(self.data)
        if self.estimation:
            self.coefficients, self.betas = self.estimate()
        else:
            parameters = pickle.load(open(f"{DIR}/results/estimations/{self.name}_{self.nested}.pickle", "rb" ))
            betas = dict()
            for beta in parameters.betas:
                betas[f"{beta.name}"] = beta.value
            self.coefficients, self.betas = parameters, betas
        self.simulation = self.simulate()
        print(self.simulation)
        self.market_shares, self.rmse = self.validate()

    def get_ms(self):
        return self.market_shares

    def get_rmse(self):
        return self.rmse

    def estimate(self):
        # Change the working directory to save the results
        os.chdir(f"{DIR}/results/estimations")

        V, av, choice = self.F.get_functions()

        if self.nested: 
            MU_ICV = Beta("MU_ICV", 1, 0, 10, 1) # Reference
            MU_BEV = Beta("MU_BEV", 1, 0, 10, 0)
            MU_PHEV = Beta("MU_PHEV", 1, 0, 10, 0)
            nest_ICV = MU_ICV, [1, 2, 3, 4, 5, 6]
            nest_BEV = MU_BEV, [7, 8, 9, 10, 11, 12]
            nest_PHEV = MU_PHEV, [13, 14, 15, 16, 17,18]
            nests = nest_ICV, nest_BEV, nest_PHEV
            logprob = models.lognested(V,av,nests,choice)

        else:
            logprob = models.loglogit(V,av,choice)

        biogeme = bio.BIOGEME(self.data.get_biogeme_database(), logprob)
        biogeme.modelName = f"{self.name}_{self.nested}"

        biogeme.generateHtml = True
        biogeme.generatePickle = True

        results = biogeme.estimate()

        pandasResults = results.getEstimatedParameters()
        betas = results.getBetaValues()

        os.chdir(WORKDIR)
        return pandasResults, betas


    def simulate(self):

        V, av, choice = self.F.get_functions()
        N = len(V)
        
        prob = dict()
        simulate = dict()
        if self.nested:
            MU_ICV = Beta("MU_ICV", 1, 0, 10, 1) # Reference
            MU_BEV = Beta("MU_BEV", 1, 0, 10, 0)
            MU_PHEV = Beta("MU_PHEV", 1, 0, 10, 0)
            nest_ICV = MU_ICV, [1, 2, 3, 4, 5, 6]
            nest_BEV = MU_BEV, [7, 8, 9, 10, 11, 12]
            nest_PHEV = MU_PHEV, [13, 14, 15, 16, 17,18]
            nests = nest_ICV, nest_BEV, nest_PHEV
             # The choice model is a logit, with availability conditions
            for n in range(N):
                prob[n+1] = models.nested(V, av, nests, n+1)
                simulate[f'Prob. {ALT_NAME[n]}'] = prob[n+1]
        else:
            # The choice model is a logit, with availability conditions
            for n in range(N):
                prob[n+1] = models.logit(V, av, n+1)
                simulate[f'Prob. {ALT_NAME[n]}'] = prob[n+1]
            
        biogeme = bio.BIOGEME(self.simulation_data.get_biogeme_test_database(), simulate)
        biogeme.modelName = self.name
        results = biogeme.simulate(theBetaValues=self.betas)
        results[f'cph'] = self.data.wide_data_test['cph']

        return results
           

    def validate(self):

        res = DataFrame()
        res['alternative'] = ALT_NAME

        y_true = self.data.get_testing_set()
        res['true_dk'] = (y_true['CHOICE'].value_counts()/y_true.shape[0]).sort_index().shift(-1)
        res['true_cph'] = (y_true.loc[y_true['cph'] == 1,'CHOICE'].value_counts()/y_true[y_true['cph'] == 1].shape[0]).sort_index().shift(-1)
        
        y_pred = self.simulation
        res['pred_dk'] = np.array(y_pred.iloc[:,:-1].mean())
        y_pred_cph = y_pred[y_pred['cph'] == 1]
        res['pred_cph'] = np.array(y_pred_cph.iloc[:,:-1].mean())

        rmse_dk = np.sqrt(((res['pred_dk'] - res['true_dk'])**2).sum()/res.shape[0])

        # Save res dataframe
        if self.data.scenario == {}:
            os.chdir(f"{DIR}/results/validations")
            res.to_csv(f"{self.name}_{self.nested}.csv")
            os.chdir(WORKDIR)
        else:
            os.chdir(f"{DIR}/results/scenarios")
            res.to_csv(f"{self.name}_{self.nested}_{next(iter(self.data.scenario))}.csv")
            os.chdir(WORKDIR)


        return res, rmse_dk

    def forecast(self,var,value):
        self.simulation_data = self.data.change_variable(var,value)
        results = self.simulate()
        return results

    

