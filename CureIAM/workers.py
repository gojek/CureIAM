"""Worker functions.
"""


from CureIAM.helpers import util
from CureIAM.plugins import util_plugins

from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

def cloud_worker(audit_key, audit_version, plugin_key, plugin_config,
                 output_queues):
    """Worker function for cloud plugins.

    This function instantiates a plugin object from the
    ``plugin_config`` dictionary. This function expects the plugin
    object to implement a ``read`` method that yields records. This
    function calls this ``read`` method to retrieve records and puts
    each record into each queue in ``output_queues``.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin_config (dict): Cloud plugin config dictionary.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.

    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('cloud_worker: %s: Started', worker_name)

    try:
        plugin = util_plugins.load(plugin_config)
        for record in plugin.read():
            record['com'] = util.merge_dicts(record.get('com', {}), {
                'audit_key': audit_key,
                'audit_version': audit_version,
                'origin_key': plugin_key,
                'origin_class': type(plugin).__name__,
                'origin_worker': worker_name,
                'origin_type': 'cloud',
            })
            for q in output_queues:
                q.put(record)

        plugin.done()

    except Exception as e:
        _log.exception('cloud_worker: %s: Failed; error: %s: %s',
                       worker_name, type(e).__name__, e)

    _log.info('cloud_worker: %s: Stopped', worker_name)


def processor_worker(audit_key, audit_version, plugin_key, plugin_config,
                 input_queue, output_queues):
    """Worker function for processor plugins.

    This function instantiates a plugin object from the
    ``plugin_config`` dictionary. This function expects the plugin
    object to implement an ``eval`` method that accepts a single record
    as a parameter and yields one or more records, and a ``done`` method
    to perform cleanup work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``eval`` method of the plugin object. Then it puts
    each record yielded by the ``eval`` method into each queue in
    ``output_queues``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the plugin object to indicate that record
    processing is over.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin_config (dict): processor plugin config dictionary.
        input_queue (multiprocessing.Queue): Queue to read records from.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.

    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('processor_worker: %s: Started', worker_name)

    try:
        plugin = util_plugins.load(plugin_config)
    except Exception as e:
        _log.exception('processor_worker: %s: Failed; error: %s: %s',
                       worker_name, type(e).__name__, e)
        _log.info('processor_worker: %s: Stopped', worker_name)
        return

    while True:
        try:
            record = input_queue.get()
            if record is None:
                _log.info('processor_worker: %s: Stopping', worker_name)
                plugin.done()
                break

            for processor_record in plugin.eval(record):
                processor_record['com'] = \
                    util.merge_dicts(processor_record.get('com', {}), {
                        'audit_key': audit_key,
                        'audit_version': audit_version,
                        'origin_key': plugin_key,
                        'origin_class': type(plugin).__name__,
                        'origin_worker': worker_name,
                        'origin_type': 'processor',
                    })

                for q in output_queues:
                    q.put(processor_record)

        except Exception as e:
            _log.exception('processor_worker: %s: Failed; error: %s: %s',
                           worker_name, type(e).__name__, e)

    _log.info('processor_worker: %s: Stopped', worker_name)


def store_worker(audit_key, audit_version, plugin_key, plugin_config,
                 input_queue):
    """Worker function for store plugins.

    This function instantiates a plugin object from the
    ``plugin_config`` dictionary. This function expects the plugin
    object to implement a ``write`` method that accepts a single record
    as a parameter and a ``done`` method to perform cleanup work in the
    end.

    This function gets records from ``input_queue`` and passes each
    record to the ``write`` method of the plugin object.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the plugin object to indicate that record
    processing is over.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin_config (dict): Store plugin config dictionary.
        input_queue (multiprocessing.Queue): Queue to read records from.

    """
    _write_worker(audit_key, audit_version, plugin_key, plugin_config,
                  input_queue, 'store')


def alert_worker(audit_key, audit_version, plugin_key, plugin_config,
                 input_queue):
    """Worker function for alert plugins.

    This function behaves like :func:`CureIAM.workers.store_worker`.
    See its documentation for details.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin_config (dict): Alert plugin config dictionary.
        input_queue (multiprocessing.Queue): Queue to read records from.

    """
    _write_worker(audit_key, audit_version, plugin_key, plugin_config,
                  input_queue, 'alert')


def _write_worker(audit_key, audit_version, plugin_key, plugin_config,
                  input_queue, worker_type):
    """Worker function for store and alert plugins.

    Arguments:
        audit_key (str): Audit key name in configuration
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin_config (dict): Store or alert plugin config dictionary.
        input_queue (multiprocessing.Queue): Queue to read records from.
        worker_type (str): Either ``'store'`` or ``'alert'``.

    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('%s_worker: %s: Started', worker_type, worker_name)

    try:
        plugin = util_plugins.load(plugin_config)
    except Exception as e:
        _log.exception('%s_worker: %s: Failed; error: %s: %s',
                       worker_type, worker_name, type(e).__name__, e)
        _log.info('%s_worker: %s: Stopped', worker_type, worker_name)
        return

    while plugin is not None:
        try:
            record = input_queue.get()
            if record is None:
                _log.info('%s_worker: %s: Stopping',
                          worker_type, worker_name)
                plugin.done()
                break

            record['com'] = util.merge_dicts(record.get('com', {}), {
                'audit_key': audit_key,
                'audit_version': audit_version,
                'target_key': plugin_key,
                'target_class': type(plugin).__name__,
                'target_worker': worker_name,
                'target_type': worker_type,
            })

            plugin.write(record)

        except Exception as e:
            _log.exception('%s_worker: %s: Failed; error: %s: %s',
                           worker_type, worker_name, type(e).__name__, e)

    _log.info('%s_worker: %s: Stopped', worker_type, worker_name)
