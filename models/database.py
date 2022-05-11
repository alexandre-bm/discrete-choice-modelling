from dataclasses import dataclass, field
import pandas as pd
from pandas import DataFrame
from biogeme.database import Database

from sklearn.model_selection import train_test_split

GEN_COLUMNS = ['alternative', 'participant', 'scenario', 'chosen']


@dataclass
class Data:
    data_path: str
    attributes: list
    characteristics: list
    scenario: dict = field(default_factory={})
    test_size: float = 0.25
    columns: list = field(init=False)
    raw_data: DataFrame = field(init=False)
    pivot_data: DataFrame = field(init=False)
    wide_data: DataFrame = field(init=False)
    wide_data_test: DataFrame = field(init=False)
    biogeme_data: Database = field(init=False)
    biogeme_test_data: Database = field(init=False)

    def __post_init__(self):
        self.columns = [*self.attributes, *self.characteristics, 'Availability']
        self.raw_data = self.preprocess_data()
        self.pivot_data = self.process_pivot_data()
        self.wide_data, self.wide_data_test = self.process_wide_data()
        self.biogeme_data, self.biogeme_test_data = self.process_biogeme_data()

    def get_biogeme_database(self):
        return self.biogeme_data

    def get_biogeme_test_database(self):
        return self.biogeme_test_data

    def shape(self):
        return self.wide_data.shape

    def get_testing_set(self):
        return self.wide_data_test

    def change_variable(self, var, value):
        self.raw_data[var] = self.raw_data[var] * (1+value)
        self.pivot_data = self.process_pivot_data()
        self.wide_data, self.wide_data_test = self.process_wide_data()
        self.biogeme_data = self.process_biogeme_data()

    def read_data(self):
        raw_data = pd.read_csv(self.data_path)
        raw_data = raw_data.drop('Unnamed: 0', axis=1)
        return raw_data

    def preprocess_data(self):
        raw_data = self.read_data()

        # Renaming characteristics
        raw_data = raw_data.rename({
            'c_Gender': 'gender',
            'c_Age': 'age',
            'c_Kom': 'commune',
            'c_Geogrp': 'geogrp',
            'c_Samplegroup': 'sample_group',
            'c_Sampletype': 'sample_type',
            'Postalcode': 'postalcode',
            'q1': 'occupation',
            'q9': 'income',
            'q8x': 'education',
            'ID': 'participant'
        }, axis='columns')

        # Renaming attributes
        raw_data = raw_data.rename({
            'ScenarioID': 'scenario',
            'AltID': 'alternative',
            'CH': 'selected_alternative'
        }, axis='columns')

        raw_data['Availability'] = 1
        raw_data['cph'] = raw_data['postalcode'].between(1000,2999, inclusive='both').astype(int)
        raw_data['ICV'] = [1 if a in [1,2,3,4,5,6] else 0 for a in raw_data['alternative']]

        # Scenario on ICV vehicle
        if self.scenario != {}:
            for key, value in self.scenario.items():
                raw_data.loc[raw_data['ICV'] == 0,key] = (1+value) * raw_data[key] 

        return raw_data

    def process_pivot_data(self):
        pivot_data = pd.pivot_table(self.raw_data, values = self.columns, index = ['participant', 'scenario'], columns = ['alternative'], fill_value = 0)
        x = self.raw_data['chosen'] * self.raw_data['alternative']
        pivot_data['CHOICE'] = x[x != 0].tolist()
        pivot_data['cph'] = self.raw_data.groupby(['participant', 'scenario']).mean()['cph']
        # Creation of the dummy variable for gender
        Male = self.raw_data.groupby(['participant', 'scenario']).first()['gender']
        pivot_data['Male'] = 1*(Male == 2)

        return pivot_data

    def process_wide_data(self):
        wide_data = pd.DataFrame()
        wide_data['Male'] = self.pivot_data['Male']
        wide_data['CHOICE'] = self.pivot_data['CHOICE']
        wide_data['cph'] = self.pivot_data['cph']
        for x in self.columns: #Add all the columns
            for i in range(1,19):
                wide_data[x+'_'+str(i)] = self.pivot_data[(x, i)]

        wide_data, wide_data_test = train_test_split(wide_data, test_size = self.test_size)

        return wide_data, wide_data_test 

    def process_biogeme_data(self):
        biogeme_data = Database('data', self.wide_data)
        biogeme_test_data = Database('test_data', self.wide_data_test)
        return biogeme_data, biogeme_test_data



