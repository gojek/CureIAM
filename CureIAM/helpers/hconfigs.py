import os
import yaml
import typing
from CureIAM.helpers import util, hlogging

from CureIAM import baseconfig #deprecating soon

from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

"""
    Will deprecated this function soon
"""
def load(config_paths):
    """Load configuration from specified configuration paths.

    Arguments:
        config_paths (list): Configuration paths.

    Returns:
        dict: A dictionary of configuration key-value pairs.

    """
    config = baseconfig.config_dict

    for config_path in config_paths:
        config_path = os.path.expanduser(config_path)
        _log.info('Looking for %s', config_path)

        if not os.path.isfile(config_path):
            continue

        _log.info('Found %s', config_path)
        with open(config_path) as f:
            new_config = yaml.safe_load(f)
            config = util.merge_dicts(config, new_config)


    return config

"""
    Creating a Singleton Config file to be called everywhere
"""
class Config(object):

    _CONFIG_FILE: typing.Optional[str] = None
    _CONFIG: typing.Optional[dict] = None

    @staticmethod
    def load(config_files = None) -> dict:

        # Use singleton pattern to store config file location/load config once
        Config._CONFIG_FILE = Config.search_configuration_files(config_files)

        with open(Config._CONFIG_FILE, 'r') as f:
            Config._CONFIG = yaml.safe_load(f)
            # config = util.merge_dicts(config, new_config)


        return Config._CONFIG

    @staticmethod
    def search_configuration_files(config_files):
        for config_file in config_files:
            config_file = os.path.expanduser(config_file)
            
            if os.path.isfile(config_file):
                _log.info('Found %s', config_file)
                return config_file

        return ""

    @staticmethod
    def get_config_file() -> str:
        return Config._CONFIG_FILE

    @staticmethod
    def get_config() -> dict:
        return Config._CONFIG

    @staticmethod
    def get_config(name) -> dict:
        return Config._CONFIG[name]

    @staticmethod
    def get_config_logger() -> dict:
        return Config._CONFIG["logger"]        
        
