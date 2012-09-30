import itertools


def filter_dict(dictionary, pred):
    """Return a dict containing only those items for which
    pred(key, value) is True.

    """
    filtered_dict = {}

    for k, v in dictionary.items():
        if pred(k, v):
            filtered_dict[k] = v

    return filtered_dict


def partition(pred, iterable):
    """Partition an iterable into a list of all elements from the
    start of the stream until `pred` returns False, and a list of all
    elements after and including the first element which does not
    match `pred`.

    """
    stream = list(iterable)
    matched = list(itertools.takewhile(pred, stream))
    unmatched = list(itertools.dropwhile(pred, stream))
    return matched, unmatched


SI_SUFFIXES = {
    '':  1000 ** 0,
    'k': 1000,
    'm': 1000 ** 2,
    'g': 1000 ** 3,
    't': 1000 ** 4,
}


def parse_value_with_si_suffix(string):
    """Convert a string containing an positive integer and a SI
    suffix (ex. 4k, 100M, 131G) into its integer representation.

    """
    digits, suffix = partition(lambda c: c.isdigit(), string)
    mantissa = int(''.join(digits))
    suffix = ''.join(suffix).lower()
    scale = SI_SUFFIXES.get(suffix)

    if scale is None:
        names = [ '"{0}"'.format(k) for k in SI_SUFFIXES.keys() ]
        if len(names) > 1:
            options = "{0} or {1}".format(', '.join(names[:-1]), names[-1])
        else:
            options = names[0]

        msg = '{0}: suffix "{1}" must be one of {2}'.format(
            string, suffix, options)

        raise ValueError(msg)

    return mantissa * scale
