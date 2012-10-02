import argparse
import os
import sys

import yaml

from s3viewport.utils import expandpath, filter_dict, map_dict, merge_dicts


# Default values for omissible settings
DEFAULT_SETTINGS = {
    'foreground': False,
    'no-input': False,

    'attribute-cache': {
        'lifetime': 3600,
    },
    'directory-cache': {
        'lifetime': 60,
    },
    'file-cache': {
        'lifetime': 3600,
        'max-bytes': '100M',
        'max-files': 1000,
    },
}


# Required setting names, and prompts for the user if they are omitted
REQUIRED_SETTINGS = {
    'mount-point': 'Mount point: ',
    'bucket':      'S3 bucket: ',
    'access-key':  'Access key: ',
    'secret-key':  'Secret key: ',
}


def read_command_line():
    """Returns a dict containing the arguments specified on the command line"""

    parser = argparse.ArgumentParser(
        description='Mount an S3 bucket as a read-only filesystem')

    # All arguments must default to None so that they can be filtered
    # out of the returned dictionary; otherwise, the argument defaults
    # will override settings from the configuration file.
    parser.add_argument('mount-point',
                        help='where to mount the bucket')
    parser.add_argument('--bucket', dest='bucket',
                        help='S3 bucket to mount')
    parser.add_argument('--access-key', dest='access-key',
                        help='access key for the bucket')
    parser.add_argument('--secret-key', dest='secret-key',
                        help='secret key for the bucket')

    parser.add_argument('--config-file', dest='config-file',
                        default='~/.s3viewport.yaml',
                        help='path to the configuration file')

    parser.add_argument('--no-input', dest='no-input',
                        action='store_true', default=None,
                        help="don't prompt for missing information")
    parser.add_argument('--foreground', dest='foreground',
                        action='store_true', default=None,
                        help='run filesystem server in the foreground')

    # TODO: Describe configuration file format

    args = parser.parse_args()
    return filter_dict(vars(args), lambda k, v: v is not None)


def read_configuration_file(path, mount_point):
    """Reads the YAML file at the location `path`, and returns a pair of
    dicts. The first dict contains the default settings for all mount points,
    while the second contains settings for the selected mount point.

    """

    path = expandpath(path)

    if not os.path.exists(path):
        return {}, {}

    with open(path, 'r') as f:
        conf = yaml.load(f)

    default_conf = conf.get('defaults', {})
    mount_points = conf.get('mount-points', {})

    # Expand all mount points to their absolute paths before comparing
    # against the selected mount point (which is already expanded.)
    mount_points = map_dict(mount_points, lambda k, v: (expandpath(k), v))
    mount_point_conf = mount_points.get(mount_point, {})

    return default_conf, mount_point_conf


def validate_missing_information(conf):
    """Validates settings in the merged dict `conf`. Prints an error if
    any settings specified in `REQUIRED_SETTINGS` are missing from `conf`.
    If any error is detected, this function causes the program to exit
    with a non-zero exit code.

    """
    failed = False

    for field, _ in REQUIRED_SETTINGS.items():
        if field not in conf:
            print 'error: missing configuration for "{0}"'.format(field)
            failed = True

    if failed:
        sys.exit(1)


def request_missing_information(conf):
    """Validates the settings in the merged dict `conf`. Prompts the user to
    enter any required settings which may have been omitted, and returns a
    copy of `conf` with the missing settings filled in.

    """
    for field, prompt in REQUIRED_SETTINGS.items():
        if field not in conf:
            conf[field] = raw_input(prompt)

    return conf


def get_configuration(defaults=DEFAULT_SETTINGS):
    """Reads command line arguments and a YAML configuration file, and
    returns a dict of settings.

    """
    # We need to read the command-line arguments first to determine the
    # configuration directory and mount point, but we merge them last
    # into the main configuration so they have the highest precedence.
    arg_conf = read_command_line()
    path = arg_conf.pop('config-file')
    mount_point = expandpath(arg_conf['mount-point'])
    arg_conf['mount-point'] = mount_point

    default_conf, mount_point_conf = read_configuration_file(path, mount_point)

    merged_conf = dict(defaults)
    merge_dicts(merged_conf, default_conf)
    merge_dicts(merged_conf, mount_point_conf)
    merge_dicts(merged_conf, arg_conf)

    if merged_conf.get('no-input', False):
        validate_missing_information(merged_conf)
    else:
        merged_conf = request_missing_information(merged_conf)

    return merged_conf
