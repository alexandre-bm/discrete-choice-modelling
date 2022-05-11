from .config import Config
from hydra.core.config_store import ConfigStore


cs = ConfigStore.instance()
cs.store(name="default_config", node=Config)