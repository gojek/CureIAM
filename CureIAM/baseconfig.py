"""Base configuration.

Attributes:
    config_yaml (str): Base configuration as YAML code.
    config_dict (dict): Base configuration as Python dictionary.

Here is the complete base configuration present as a string in the
:obj:`config_yaml` attribute::

{}

"""

import textwrap

import yaml

config_yaml = """# Base configuration
logger:
  version: 1

  disable_existing_loggers: false

  formatters:
    simple:
      format: >-
          %(asctime)s [%(process)s] [%(processName)s] [%(threadName)s]
          %(levelname)s %(name)s:%(lineno)d - %(message)s
      datefmt: "%Y-%m-%d %H:%M:%S"

  handlers:
    rich_console:
      class: rich.logging.RichHandler
      formatter: simple

    console:
      class: logging.StreamHandler
      formatter: simple
      stream: ext://sys.stdout

    file:
      class: logging.handlers.TimedRotatingFileHandler
      formatter: simple
      filename: /tmp/CureIAM.log
      when: midnight
      encoding: utf8
      backupCount: 5

  loggers:
    adal-python:
      level: WARNING

  root:
    level: INFO
    handlers:
      - rich_console
      - file
  
  child:
    level: INFO
    handlers: 
      - rich_console
    qualname: child
    propagate: 0


schedule: "00:00"
"""


config_dict = yaml.safe_load(config_yaml)
__doc__ = __doc__.format(textwrap.indent(config_yaml, '    '))
