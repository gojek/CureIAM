import importlib
from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

def load(plugin_config):
    """Construct an object with specified plugin class and parameters.

    The ``plugin_config`` parameter must be a dictionary with the
    following keys:

    - ``plugin``: The value for this key must be a string that
      represents the fully qualified class name of the plugin. The
      fully qualified class name is in the dotted notation, e.g.,
      ``pkg.module.ClassName``.
    - ``params``: The value for this key must be a :obj:`dict` that
      represents the parameters to be passed to the ``__init__`` method
      of the plugin class. Each key in the dictionary represents the
      parameter name and each value represents the value of the
      parameter.

    Example:
        Here is an example usage of this function:

        >>> from CureIAM import util
        >>> plugin_config = {
        ...     'plugin': 'CureIAM.clouds.mockcloud.MockCloud',
        ...     'params': {
        ...         'record_count': 4,
        ...         'record_types': ('baz', 'qux')
        ...     }
        ... }
        ...
        >>> plugin = util.load_plugin(plugin_config)
        >>> print(type(plugin))
        <class 'CureIAM.clouds.mockcloud.MockCloud'>
        >>> for record in plugin.read():
        ...     print(record['raw']['data'],
        ...           record['ext']['record_type'],
        ...           record['com']['record_type'])
        ...
        0 baz mock
        1 qux mock
        2 baz mock
        3 qux mock

    Arguments:
        plugin_config (dict): Plugin configuration dictionary.

    Returns:
        object: An object of type mentioned in the ``plugin`` parameter.

    Raises:
        PluginError: If plugin class name is invalid.

    """
    # Split the fully qualified class name into module and class names.
    parts = plugin_config['plugin'].rsplit('.', 1)

    # Validate that the fully qualified class name had at least two
    # parts: module name and class name.
    if len(parts) < 2:
        msg = ('Invalid plugin class name: {}; expected format: '
               '[<pkg>.]<module>.<class>'.format(plugin_config['plugin']))
        raise PluginError(msg)

    # Load the specified adapter class from the specified module.
    plugin_module = importlib.import_module(parts[0])
    plugin_class = getattr(plugin_module, parts[1])

    # Initialize params to empty dictionary if none was specified.
    plugin_params = plugin_config.get('params', {})

    # Construct the plugin.
    plugin = plugin_class(**plugin_params)
    return plugin


class PluginError(Exception):
    """Represents an error while loading a plugin."""
