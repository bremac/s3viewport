import collections
import itertools
import os


def expandpath(path):
    """Return the absolute path corresponding to `path` after expanding
    home directories and relative paths.

    """
    return os.path.abspath(os.path.expanduser(path))



def filter_dict(dictionary, pred):
    """Return a dict containing only those items for which
    pred(key, value) is True.

    """
    return dict((k, v) for k, v in dictionary.items() if pred(k, v))


def map_dict(dictionary, transform):
    """Return a dict containing the results of applying transform(k, v)
    to all items in the dictionary.

    """
    return dict(transform(k, v) for k, v in dictionary.items())


def merge_dicts(dest, src):
    """Recursively merge two dicts together, such that all non-dictionary
    values in `dest` are replaced with those in `src`, but all dict values in
    `dest` are merged with the corresponding dict in `src`.

    """

    for k, v in src.items():
        if isinstance(v, collections.Mapping):
            dest_v = dest.get(k, {})
            if not isinstance(dest_v, collections.Mapping):
                msg = "Attempted to merge {0!r} with {1!r}".format(dest_v, v)
                raise TypeError(msg)

            dest[k] = merge_dicts(dest_v, v)
        else:
            dest[k] = src[k]

    return dest


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
    """Convert a string containing a positive integer and a SI
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
