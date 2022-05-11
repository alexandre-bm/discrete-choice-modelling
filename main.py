import hydra 
import logging
import os

from src import Config, Debug
from models import Data, UtiliyFunction, Model

DIR = os.path.dirname(os.path.realpath(__file__))

def ModelFactory(config, log) -> Model:

    name = config.params.name
    data_path = config.params.data_path
    attributes = config.params.attributes
    characteritics = config.params.characteristics
    scenario = config.params.scenario
    nested = config.params.nested
    estimation = config.params.estimation

    database = Data(DIR + "/" + data_path, attributes, characteritics, scenario)
    log.info(f"Data loaded, shape is {database.shape()}")

    F =  UtiliyFunction(18, database, attributes, characteritics)
    log.info(f'Utility functions created')

    model = Model(name, database, F, nested, estimation)
    log.info(f'Model estimated')
    
    return model

@hydra.main(config_path="src/config", config_name="config")
def main(config: Config):
    log = Debug(__name__, config, logging.INFO).__run__()
    model = ModelFactory(config, log)
    ms = model.get_ms()
    rmse = model.get_rmse()
    print(f"RMSE = {rmse}")

if __name__ == '__main__':
    main()

