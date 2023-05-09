import logging.config
import logging
import copy
import json
import typing
from multiprocessing import current_process

DEFAULT_LOGGING_CONFIG = { #temporary config for logging, will move it to yaml file in the future
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'main': { 
            'format': '[%(asctime)s][%(process)s][%(processName)s][%(threadName)s] - %(levelname)s %(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'standard': { 
            'format': '[%(process)s][%(processName)s][%(threadName)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': { 
        'main': { 
            'formatter': 'main',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'console': { 
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'rich': { 
            'formatter': 'standard',
            'class': 'rich.logging.RichHandler',
        },
        'file': { 
            'formatter': 'standard',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/tmp/CureIAM.log',
            'when': 'midnight',
            'encoding': 'utf8',
            'backupCount': 5,
        },  
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        'CureIAM.plugins.gcp.*': { 
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        'CureIAM.plugins.gcp.gcpcloud': { #temporary solution adding file one by one till we've found the way to log properly
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        'CureIAM.plugins.elastic.esstore': { #temporary solution adding file one by one till we've found the way to log properly
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        'CureIAM.plugins.files.filestore': { #temporary solution adding file one by one till we've found the way to log properly
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        'CureIAM.ioworkers': { #temporary solution adding file one by one till we've found the way to log properly
            'handlers': ['file','rich'],
            'level': 'INFO',
            'propagate': False
        },
        # 'CureIAM.helpers.hconfigs': { 
        #     'handlers': ['rich'],
        #     'level': 'INFO',
        #     'propagate': False
        # }
    } 
}

"""
    Will deprecated this function soon, BETA Testing
"""
def get_logger(name):
    # process_name = current_process()
    # print (current_process())
    logging_config = None

    if logging_config == None:
        logging_config = DEFAULT_LOGGING_CONFIG        

    logging.config.dictConfig(logging_config)

    return logging.getLogger(name)

def obfuscated(data): #it only for demo purposed
    len_data = len(data)
    idx = data.find('-')

    temp = data[0:2] + ('*'*(len_data-2))

    return temp


"""
    Creating a Singleton logging class to be called everywhere
"""
class Logger(object):
    """Creating for logging purpose only"""

    _LOG_CONFIG: typing.Optional[dict] = None
        
    @staticmethod
    def set_logger(log_config):
        # print (log_config)
        Logger._LOG_CONFIG = log_config

    @staticmethod
    def get_logger(name):
        logging_config = Logger._LOG_CONFIG

        if logging_config == None:
            logging_config = DEFAULT_LOGGING_CONFIG        

        logging.config.dictConfig(logging_config)

        return logging.getLogger(name)