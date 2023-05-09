#default library
import argparse
import textwrap

#custom class
import CureIAM

from CureIAM.helpers import util

def parse(args=None):
    """Parse command line arguments.

    Arguments:
        args (list): List of command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.

    """
    default_config_paths = [
        '/etc/CureIAM.yaml',
        '~/.CureIAM.yaml',
        '~/CureIAM.yaml',
        'CureIAM.yaml',
    ]

    description = """
    \033[34m========================================================\033[0m
          
           \033[91m_____               _____          __  __\033[0m
          \033[91m/ ____|             |_   _|   /\   |  \/  |\033[0m
         \33[93m| |    _   _ _ __ ___  | |    /  \  | \  / |\033[0m
         \33[93m| |   | | | | '__/ _ \ | |   / /\ \ | |\/| |\033[0m
         \33[34m| |___| |_| | | |  __/_| |_ / ____ \| |  | |\033[0m
          \33[34m\_____\__,_|_|  \___|_____/_/    \_\_|  |_|\033[0m

    \033[34m========================================================\033[0m
    \033[91mAudit clouds as specified by configuration.\033[0m

    [*] Audit clouds as specified by configuration - Automated IAM Recommender 
    [*] Based on Google IAM Cloud Recommender
    [*] Credits: Gojek Security Team
    [*] Author: Rohit S & Kenny G
    [*] Source: https://github.com/gojek/CureIAM

    \033[91mUsage:\033[0m
        python3 -m CureIAM [options]

    \033[91mExamples:\033[0m
        python3 -m CureIAM -n 
        python3 -m CureIAM -c CureIAM.yaml
        python3 -m CureIAM

    Zero or more config files are specified with the -c/--config option.
    The config files specified are merged with a built-in base config.
    Use the -p/--print-base-config option to see the built-in base
    config. Missing config files are ignored.

    If two or more config files provide conflicting config values, the
    config file specified later overrides the built-in base config and
    the config files specified earlier.

    If the -c/--config option is specified without any file arguments
    following it, then only the built-in base config is used.

    If the -c/--config option is omitted, then the following config
    files are searched for and merged with the built-in base config: {}.
    Missing config files are ignored.
    """
    description = description.format(util.friendly_list(default_config_paths))
    description = description

    # We will use this format to preserve formatting of the description
    # above with the newlines and blank lines intact. The default
    # formatter line-wraps the entire description after ignoring any
    # superfluous whitespace including blank lines, so the paragraph
    # breaks are lost, and the usage description looks ugly.
    formatter = argparse.RawDescriptionHelpFormatter

    parser = argparse.ArgumentParser(prog='CureIAM',
                                     description=description,
                                     formatter_class=formatter)

    parser.add_argument('-c', '--config', nargs='*',
                        default=default_config_paths,
                        help='run audits with specified configuration files')

    parser.add_argument('-n', '--now', action='store_true',
                        help='ignore configured schedule and run audits now')

    parser.add_argument('-p', '--print-base-config', action='store_true',
                        help='print base configuration')

    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + CureIAM.__version__)

    args = parser.parse_args(args)
    return args