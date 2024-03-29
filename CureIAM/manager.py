#!/usr/bin/env python

"""Manager of worker subprocesses.

This module invokes the worker subprocesses that perform the cloud
security monitoring tasks. Each worker subprocess wraps around a cloud,
store, processor, or alert plugin and executes the plugin in a separate
subprocess.
"""

import multiprocessing as mp

import copy
import textwrap
import time
import json

#for scheduling
import schedule

# import pprint

""" . = CureIAM which is the current module, for now it changes, to remove any depedency name incase if there is any changes folder name in the future
"""
import CureIAM
from CureIAM import baseconfig, workers
from CureIAM.helpers import hconfigs, hemails, hcmd
from CureIAM.helpers.hconfigs import Config

from CureIAM.helpers import hlogging
# from CureIAM.helpers.hlogging import Logger

_log = hlogging.get_logger(__name__)

def main():
    """Run the framework based on the schedule."""
    # Configure the logger as the first thing as per the base
    # configuration. We need this to be the first thing, so that

    # Parse the command line arguments and handle the options that can
    # be handled immediately.
    args = hcmd.parse()
    if args.print_base_config:
        print(baseconfig.config_yaml.strip())
        return

    # Now load user's configuration files.
    # config = hconfigs.load(args.config)
    
    # print (config)

    # set up the configuration 
    config = Config.load(args.config)
    # Logger.set_logger(Config.get_config_logger())

    # Then configure the logger once again to honour any logger
    # configuration defined in the user's configuration files.
    # logging.config.dictConfig(config['logger'])
    _log.info('CureIAM %s; configured', CureIAM.__version__)

    # Finally, run the audits, either right now or as per a schedule,
    # depending on the command line options.
    if args.now:
        _log.info('Starting job now')
        _run(config)
    else:
        _log.info('Scheduled to run job everyday at %s', config['schedule'])
        schedule.every().day.at(config['schedule']).do(_run, config)
        while True:
            schedule.run_pending()
            time.sleep(60)


def _run(config):
    """Run the audits.

    Arguments:
        config (dict): Configuration dictionary.

    """
    start_time = time.localtime()
    _send_email(config.get('email'), 'all audits', start_time)

    # Create an audit object for each audit configured to be run.
    audit_version = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
    audits = []
    for audit_key in config['run']:
        audits.append(Audit(audit_key, audit_version, config))

    # Start all audits.
    for audit in audits:
        audit.start()

    # Wait for all audits to terminate.
    for audit in audits:
        audit.join()

    end_time = time.localtime()
    _send_email(config.get('email'), 'all audits', start_time, end_time)


class Audit:
    """Audit manager.

    This class encapsulates a set of worker subprocesses and worker
    input queues for a single audit configuration.
    """

    def __init__(self, audit_key, audit_version, config):
        """Create an instance of :class:`Audit` from configuration.

        A single audit definition (from a list of audit definitions
        under the ``audits`` key in the configuration) is instantiated.
        Each audit definition contains lists of cloud plugins, store
        plugins, processor plugins, and alert plugins. These plugins are
        instantiated and multiprocessing queues are set up to take
        records from one plugin and feed them to another plugin as per
        the audit workflow.

        Arguments:
            audit_key (str): Key name for an audit configuration. This
                key is looked for in ``config['audits']``.
            audit_version (str): Audit version string.
            config (dict): Configuration dictionary. This is the
                entire configuration dictionary that contains
                top-level keys named ``clouds``, ``stores``, ``processors``,
                ``alerts``, ``audits``, ``run``, etc.

        """
        self._start_time = time.localtime()
        self._audit_key = audit_key
        self._audit_version = audit_version
        self._config = config
        self._audit_config = config['audits'][audit_key]
        audit_config = config['audits'][audit_key]

        # We keep all workers in these lists.
        self._cloud_workers = []
        self._store_workers = []
        self._processor_workers = []
        self._alert_workers = []

        # We keep all queues in these lists.
        self._store_queues = []
        self._processor_queues = []
        self._alert_queues = []

        # Create alert workers and queues.
        for plugin_key in audit_config.get('alerts', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                config['plugins'][plugin_key],
                input_queue,
            )
            worker = mp.Process(target=workers.alert_worker, args=args)
            self._alert_workers.append(worker)
            self._alert_queues.append(input_queue)

        # Create processor_workers workers and queues.
        for plugin_key in audit_config.get('processors', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                config['plugins'][plugin_key],
                input_queue,
                self._store_queues,
            )
            worker = mp.Process(target=workers.processor_worker, args=args)
            self._processor_workers.append(worker)
            self._processor_queues.append(input_queue)

        # Create store workers and queues.
        for plugin_key in audit_config.get('stores', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                config['plugins'][plugin_key],
                input_queue,
            )
            worker = mp.Process(target=workers.store_worker, args=args)
            self._store_workers.append(worker)
            self._store_queues.append(input_queue)

        # Create cloud workers.
        for plugin_key in audit_config.get('clouds', []):
            args = (
                audit_key,
                audit_version,
                plugin_key,
                config['plugins'][plugin_key],
                self._processor_queues
            )
            worker = mp.Process(target=workers.cloud_worker, args=args)
            self._cloud_workers.append(worker)

    def start(self):
        """Start audit by starting all workers."""
        _send_email(self._config.get('email'), self._audit_key,
                    self._start_time)

        # Start store and alert workers.
        for w in self._store_workers + self._alert_workers:
            w.start()

        # Start cloud and processor workers.
        for w in self._cloud_workers + self._processor_workers:
            w.start()

        # It would have been nice if we could guarantee that the
        # begin_audit records are sent to each store and alert before
        # any cloud or processor records are sent. But this is difficult to
        # achieve because we must avoid forking a multithreaded process.
        #
        # See https://stackoverflow.com/q/55924761 for more details on
        # why a multihreaded process should not be forked.
        #
        # The q.put() call starts a feeder thread, thus making the
        # current process mulithreaded. Therefore, any forking (the
        # w.start() calls) must be done prior to q.put() calls.
        #
        # As a result, we make the q.put() calls *after* starting the
        # cloud workers. This means that it is not guaranteed that
        # begin_audit record is the very first record that would be
        # received by each store and alert plugin. However, the
        # begin_audit record would be one of the several earliest
        # records received by the plugins.

    def join(self):
        """Wait until all workers terminate."""
        # Wait for cloud workers to terminate.
        for w in self._cloud_workers:
            w.join()

        # Stop processor workers.
        for q in self._processor_queues:
            q.put(None)

        # Wait for processor workers to terminate.
        for w in self._processor_workers:
            w.join()

        # Stop store workers.
        for q in self._store_queues:
            q.put(None)

        # Wait for store workers to terminate.
        for w in self._store_workers:
            w.join()

        # Stop alert workers.
        for q in self._alert_queues:
            q.put(None)

        # Wait for alert workers to terminate.
        for w in self._alert_workers:
            w.join()

        end_time = time.localtime()
        _send_email(self._config.get('email'), self._audit_key,
                    self._start_time, end_time)
        
        # If Audit results has to be enforced, check if in the 
        # current audit confi the applyRecommendations is set
        # to true
        if self._audit_config.get('applyRecommendations', False):
            _log.info('Apply recommendations gracefully ...')



def _send_email(email_config, about, start_time, end_time=None):
    """Send email about job or audit that is starting or ending.

    Arguments:
        email_config (dict): Top-level email configuration dictionary.
        about (str): A short string that says what the email
            notification is about, e.g., ``'job'`` or ``'audit'``.
        start_time (time.struct_time): Start time of job or audit.
        end_time (time.struct_time): End time of job or audit. This
            argument must not be specified if the job or audit is
            starting.

    """
    state = 'starting' if end_time is None else 'ending'
    # if email_config is None:
    #     _log.info('Skipping email notification because email config is '
    #               'missing; about: %s; state: %s', about, state)
    #     return

    _log.info('Sending email; about: %s; state: %s', about, state)

    # This part of the content is common for both starting and
    # ending states.
    time_fmt = '%Y-%m-%d %H:%M:%S %z (%Z)'
    content = """
    About: {}
    Started: {}
    """.format(about, time.strftime(time_fmt, start_time))
    content = textwrap.dedent(content).lstrip()

    # This part of the content is added only for ending state.
    if state == 'ending':
        duration = time.mktime(end_time) - time.mktime(start_time)
        mm, ss = divmod(duration, 60)
        hh, mm = divmod(mm, 60)

        end_content = """
        Ended: {}
        Duration: {:02.0f} h {:02.0f} m {:02.0f} s
        """.format(time.strftime(time_fmt, end_time), hh, mm, ss)

        content = content + textwrap.dedent(end_content).lstrip()


    # hemails.send(content=content, **email_config)
    print(content)
    _log.info('Sent email; about: %s; state: %s', about, state)
