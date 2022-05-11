from dataclasses import dataclass, field
from biogeme.expressions import Variable
from biogeme.expressions import Beta
from models.database import Data

ALT_NAME = ['ICV_MINI', 'ICV_LIL', 'ICV_MEL', 'ICV_STOR', 'ICV_PREM', 'ICV_LUK', 
            'BEV_MINI', 'BEV_LIL', 'BEV_MEL', 'BEV_STOR', 'BEV_PREM', 'BEV_LUK',
            'PHEV_MINI', 'PHEV_LIL', 'PHEV_MEL', 'PHEV_STOR', 'PHEV_PREM', 'PHEV_LUK']

@dataclass
class UtiliyFunction:
    N: int
    data: Data
    attributes: list
    characteristics: list
    ASC: dict = field(init=False)
    Betas: dict = field(init=False)
    V: dict = field(init=False)
    AV: dict = field(init=False)
    choice: Variable = field(init=False)
    cph: Variable = field(init=False)
    bev: Variable = field(init=False)
    phev: Variable = field(init=False)

    def __post_init__(self):
        globals().update(self.data.get_biogeme_database().variables)
        self.choice = globals()['CHOICE']
        self.cph = globals()['cph']
        self.bev = [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0]
        self.phev = [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1]
        self.ASC = self.asc()
        self.Betas = self.betas()
        self.AV = self.availabilities()
        self.V = self.functions()
        
    def get_functions(self):
        return self.V, self.AV, self.choice

    def asc(self):
        ASC = dict()
        for n in range(1,self.N):
            ASC[n] = Beta(f'ASC_{ALT_NAME[n-1]}', 0, None, None, 0)
        ASC[self.N] = Beta(f'ASC_{ALT_NAME[self.N-1]}', 0, None, None, 1)
        return ASC

    def betas(self):
        Betas = dict()
        for (n,col) in enumerate([*self.attributes, *self.characteristics]):
            if col in self.characteristics:
                Betas[n] = {'dk_BEV': Beta(f'BETA_{col}_dk_BEV',0,None,None,0),
                            'dk_PHEV': Beta(f'BETA_{col}_dk_PHEV',0,None,None,0),
                            'cph_BEV': Beta(f'BETA_{col}_cph_BEV',0,None,None,0),
                            'cph_PHEV': Beta(f'BETA_{col}_cph_PHEV',0,None,None,0)}
            else:
                Betas[n] = {'dk': Beta(f'BETA_{col}_dk',0,None,None,0),
                            'cph': Beta(f'BETA_{col}_cph',0,None,None,0)}
        return Betas
        
    def availabilities(self):
        av = dict()
        for n in range(1,self.N+1):
            av[n] = globals()[f'Availability_{n}']
        return av 

    def functions(self):
        VAR = []
        for col in [*self.attributes, *self.characteristics]:
            for j in range(self.N):
                VAR.append(globals()[''.join((col,'_',str(j+1)))])
        U = dict()
        A = len(self.attributes)
        for n in range(6):
            U[n] = self.ASC[n+1] + sum([self.Betas[i]['dk'] * VAR[self.N*i + n] + self.Betas[i]['cph'] * VAR[self.N*i + n] * self.cph for i in range(len(self.attributes))])
        for n in range(6,self.N):
            U[n] = self.ASC[n+1] + sum([self.Betas[i]['dk'] * VAR[self.N*i + n] + self.Betas[i]['cph'] * VAR[self.N*i + n] * self.cph for i in range(len(self.attributes))])
            U[n] += sum([self.Betas[A + i]['dk_BEV'] * VAR[self.N*(A+i) + n] * self.bev[n] + self.Betas[A+i]['dk_PHEV'] * VAR[self.N*(A+i) + n] * self.phev[n] + self.Betas[A+i]['cph_BEV'] * VAR[self.N*(A+i) + n] * self.bev[n] * self.cph + self.Betas[A+i]['cph_PHEV'] * VAR[self.N*(A+i) + n] * self.phev[n] * self.cph for i in range(len(self.characteristics))])
        #U[self.N-1] = self.ASC[self.N-1] + sum([self.Betas[i]['dk'] * VAR[self.N*i + self.N-1] + self.Betas[i]['cph'] * VAR[self.N*i + self.N-1] * self.cph for i in range(len(self.attributes))]) # + sum([self.Betas[len(self.attributes)+i][self.N-1] * VAR[self.N*len(self.attributes) + self.N*i + self.N-1] for i in range(len(self.characteristics))]) # Reference
        V = dict({n+1: U[n] for n in range(self.N)})
        return V


