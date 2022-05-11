from dataclasses import dataclass, field
import sys, os
from models import database
from models.database import Data
from models.utility_function import UtiliyFunction
from models.model import Model

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src.config import Config
from src.debug import Debug

DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

@dataclass
class Factory:
    config: Config
    log: Debug
        

class DBFactory(Factory):
    db: Data = field(init=False)
    
    def __post_init__(self):
        data_path = self.config.params.data_path
        attributes = self.config.params.attributes
        characteristics = self.config.params.characteristics
        self.db = Data(DIR + "/" + data_path, attributes, characteristics)
        return self.db


class UFFactory(Factory):
    db: Data = field(init=False)
    uf: UtiliyFunction = field(init=False)
    
    def __post_init__(self):
        attributes = self.config.params.attributes
        characteristics = self.config.params.characteristics
        self.db = DBFactory(self.config, self.log)
        self.uf = UtiliyFunction(18, database, attributes, characteristics)
        return self.uf


class ModelFactory(Factory):
    db: Data = field(init=False)
    uf: UtiliyFunction = field(init=False)
    model: Model = field(init=False)

    def __post_init__(self):
        print("In the post_init method")
        self.db = DBFactory(self.config, self.log)
        self.uf = UFFactory(self.config, self.log)
        self.model = Model(self.db, self.uf)
        print("In the class builder: ", self.model)
        return self.model

