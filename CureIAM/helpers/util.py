"""Utility functions."""

import argparse
import copy
import importlib
import textwrap

from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

def wrap_paragraphs(text, width=70):
    """Wrap each paragraph in ``text`` to the specified ``width``.

    If the ``text`` is indented with any common leading whitespace, then
    that common leading whitespace is removed from every line in text.
    Further, any remaining leading and trailing whitespace is removed.
    Finally, each paragraph is wrapped to the specified ``width``.

    Arguments:
        text (str): String containing paragraphs to be wrapped.
        width (int): Maximum length of wrapped lines.

    """
    # Remove any common leading indentation from all lines.
    text = textwrap.dedent(text).strip()

    # Split the text into paragraphs.
    paragraphs = text.split('\n\n')

    # Wrap each paragraph and join them back into a single string.
    wrapped = '\n\n'.join(textwrap.fill(p, width) for p in paragraphs)
    return wrapped

def _merge_dicts(a, b):
    """Recursively merge two dictionaries.

    Arguments:
        a (dict): First dictionary.
        b (dict): Second dictionary.

    Returns:
        dict: Merged dictionary.

    """
    c = copy.deepcopy(a)
    for k in b:
        if (k in a and isinstance(a[k], dict) and isinstance(b[k], dict)):
            c[k] = merge_dicts(a[k], b[k])
        else:
            c[k] = copy.deepcopy(b[k])
    return c


def merge_dicts(*dicts):
    """Recursively merge dictionaries.

    The input dictionaries are not modified. Given any
    number of dicts, deep copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.

    Example:
        Here is an example usage of this function:

        >>> from CureIAM import util
        >>> a = {'a': 'apple', 'b': 'ball'}
        >>> b = {'b': 'bat', 'c': 'cat'}
        >>> c = util.merge_dicts(a, b)
        >>> print(c == {'a': 'apple', 'b': 'bat', 'c': 'cat'})
        True


    Arguments:
        *dicts (dict): Variable length dictionary list

    Returns:
        dict: Merged dictionary

    """
    result = {}
    for dictionary in dicts:
        result = _merge_dicts(result, dictionary)
    return result


def expand_port_ranges(port_ranges):
    """Expand ``port_ranges`` to a :obj:`set` of ports.

    Examples:
        Here is an example usage of this function:

        >>> from CureIAM import util
        >>> ports = util.expand_port_ranges(['22', '3389', '8080-8085'])
        >>> print(ports == {22, 3389, 8080, 8081, 8082, 8083, 8084, 8085})
        True
        >>> ports = util.expand_port_ranges(['8080-8084', '8082-8086'])
        >>> print(ports == {8080, 8081, 8082, 8083, 8084, 8085, 8086})
        True

        Note that in a port range of the form ``m-n``, both ``m`` and
        ``n`` are included in the expanded port set. If ``m > n``, we
        get an empty port set.

        >>> ports = util.expand_port_ranges(['8085-8080'])
        >>> print(ports == set())
        True

        If an invalid port range is found, it is ignored.

        >>> ports = util.expand_port_ranges(['8080', '8081a', '8082'])
        >>> print(ports == {8080, 8082})
        True
        >>> ports = util.expand_port_ranges(['7070-7075', '8080a-8085'])
        >>> print(ports == {7070, 7071, 7072, 7073, 7074, 7075})
        True

    Arguments:
        port_ranges (list): A list of strings where each string is a
            port number (e.g., ``'80'``) or port range (e.g., ``80-89``).

    Returns:
        set: A set of integers that represent the ports specified
            by ``port_ranges``.

    """
    # The return value is a set of ports, so that every port number
    # occurs only once even if they are found multiple times in
    # overlapping port ranges, e.g., ['8080-8084', '8082-8086'].
    expanded_port_set = set()

    for port_range in port_ranges:
        # If it's just a port number, e.g., '80', add it to the result set.
        if port_range.isdigit():
            expanded_port_set.add(int(port_range))
            continue

        # Otherwise, it must look like a port range, e.g., '1024-9999'.
        if '-' not in port_range:
            continue

        # If it looks like a port range, it must be two numbers
        # with a hyphen between them.
        start_port, end_port = port_range.split('-', 1)
        if not start_port.isdigit() or not end_port.isdigit():
            continue

        # Add the port numbers in the port range to the result set.
        expanded_ports = range(int(start_port), int(end_port) + 1)
        expanded_port_set.update(expanded_ports)

    return expanded_port_set


def friendly_string(technical_string):
    """Translate a technical string to a human-friendly phrase.

    In most of our code, we use succint strings to express various
    technical details, e.g., ``'gcp'`` to express Google Cloud Platform.
    However these technical strings are not ideal while writing
    human-friendly messages such as a description of a security issue
    detected or a recommendation to remediate such an issue.

    This function helps in converting such technical strings into
    human-friendly phrases that can be used in strings intended to be
    read by end users (e.g., security analysts responsible for
    protecting their cloud infrastructure) of this project.

    Examples:
        Here are a few example usages of this function:

        >>> from CureIAM import util
        >>> util.friendly_string('azure')
        'Azure'
        >>> util.friendly_string('gcp')
        'Google Cloud Platform (GCP)'

    Arguments:
        technical_string (str): A technical string.

    Returns:
        str: Human-friendly string if a translation from a technical
            string to friendly string exists; the same string otherwise.

    """
    phrase_map = {
        'azure': 'Azure',
        'gcp': 'Google Cloud Platform (GCP)',
        'mysql_server': 'MySQL Server',
        'postgresql_server': 'PostgreSQL Server'
    }
    return phrase_map.get(technical_string, technical_string)


def friendly_list(items, conjunction='and'):
    """Translate a list of items to a human-friendly list of items.

    Examples:
        Here are a few example usages of this function:

        >>> from CureIAM import util
        >>> util.friendly_list([])
        'none'
        >>> util.friendly_list(['apple'])
        'apple'
        >>> util.friendly_list(['apple', 'ball'])
        'apple and ball'
        >>> util.friendly_list(['apple', 'ball', 'cat'])
        'apple, ball, and cat'
        >>> util.friendly_list(['apple', 'ball'], 'or')
        'apple or ball'
        >>> util.friendly_list(['apple', 'ball', 'cat'], 'or')
        'apple, ball, or cat'

    Arguments:
        items (list): List of items.
        conjunction (str): Conjunction to be used before the last item
            in the list; ``'and'`` by default.

    Returns:
        str: Human-friendly list of items with correct placement of
        comma and conjunction.

    """
    if not items:
        return 'none'

    items = [str(item) for item in items]

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return items[0] + ' ' + conjunction + ' ' + items[1]

    return ', '.join(items[:-1]) + ', ' + conjunction + ' ' + items[-1]


def pluralize(count, word, *suffixes):
    """Convert ``word`` to plural form if ``count`` is not ``1``.

    Examples:
        In the simplest form usage, this function just adds an ``'s'``
        to the input word when the plural form needs to be used.

        >>> from CureIAM import util
        >>> util.pluralize(0, 'apple')
        'apples'
        >>> util.pluralize(1, 'apple')
        'apple'
        >>> util.pluralize(2, 'apple')
        'apples'

        The plural form of some words cannot be formed merely by adding
        an ``'s'`` to the word but requires adding a different suffix.
        For such cases, provide an additional argument that specifies
        the correct suffix.

        >>> util.pluralize(0, 'potato', 'es')
        'potatoes'
        >>> util.pluralize(1, 'potato', 'es')
        'potato'
        >>> util.pluralize(2, 'potato', 'es')
        'potatoes'

        The plural form of some words cannot be formed merely by adding
        a suffix but requires removing a suffix and then adding a new
        suffix. For such cases, provide two additional arguments: one
        that specifies the suffix to remove from the input word and
        another to specify the suffix to add.

        >>> util.pluralize(0, 'sky', 'y', 'ies')
        'skies'
        >>> util.pluralize(1, 'sky', 'y', 'ies')
        'sky'
        >>> util.pluralize(2, 'sky', 'y', 'ies')
        'skies'

    Returns:
        str: The input ``word`` itself if ``count`` is ``1``; plural
            form of the ``word`` otherwise.

    """
    if not suffixes:
        remove, append = '', 's'
    elif len(suffixes) == 1:
        remove, append = '', suffixes[0]
    elif len(suffixes) == 2:
        remove, append = suffixes[0], suffixes[1]
    else:
        raise PluralizeError('Surplus argument: {!r}'.format(suffixes[2]))

    if count == 1:
        return word

    if remove != '' and word.endswith(remove):
        word = word[:-len(remove)]
    word = word.rstrip(remove)
    return word + append

def outline_az_sub(sub_index, sub, tenant):
    """Return a summary of an Azure subscription for logging purpose.

    Arguments:
        sub_index (int): Subscription index.
        sub (Subscription): Azure subscription model object.
        tenant (str): Azure Tenant ID.

    Returns:
        str: Return a string that can be used in log messages.

    """
    return ('subscription #{}: {} ({}) ({}); tenant: {}'
            .format(sub_index, sub.get('subscription_id'),
                    sub.get('display_name'), sub.get('state'), tenant))

class PluralizeError(Exception):
    """Represents an error while converting a word to plural form."""
