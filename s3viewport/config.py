import argparse
import getpass
import os
import sys

import yaml

from s3viewport.utils import filter_dict, map_dict


REQUIRED_FIELDS = (
    # setting        prompt          input method
    ('mount-point', 'Mount point: ', raw_input),
    ('bucket',      'S3 bucket: ',   raw_input),
    ('access-key',  'Access key: ',  raw_input),
    ('secret-key',  'Secret key: ',  getpass.getpass),
)


def read_command_line(merged_conf={}):
    parser = argparse.ArgumentParser(description='TODO: Description')

    # TODO: Describe the utility

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
                        default=False, action='store_true',
                        help="don't prompt for missing information")
    parser.add_argument('--foreground', dest='foreground',
                        default=False, action='store_true',
                        help='run filesystem server in the foreground')

    # TODO: Describe configuration file format

    args = parser.parse_args()
    arg_conf = filter_dict(vars(args), lambda k, v: v is not None)
    merged_conf.update(arg_conf)

    return merged_conf


def read_configuration_file(path, mount_point, merged_conf={}):
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return merged_conf

    with open(path, 'r') as f:
        conf = yaml.load(f)

    default_conf = conf.get('defaults', {})
    mount_points = conf.get('mount-points', {})

    # Expand all mount points to their absolute paths before comparing
    # against the selected mount point (which is already expanded.)
    mount_points = map_dict(mount_points,
                            lambda k, v: (os.path.expanduser(k), v))

    mount_point_conf = mount_points.get(mount_point, {})
    merged_conf.update(default_conf)
    merged_conf.update(mount_point_conf)

    return merged_conf


def validate_missing_information(conf):
    failed = False

    for field, _, _ in REQUIRED_FIELDS:
        if field not in conf:
            print 'error: missing configuration for "{0}"'.format(field)
            failed = True

    if failed:
        sys.exit(1)


def request_missing_information(conf):
    for field, prompt, method in REQUIRED_FIELDS:
        if field not in conf:
            conf[field] = method(prompt)

    return conf


def get_configuration(defaults={}):
    merged_conf = dict(defaults)
    merged_conf = read_command_line(merged_conf)

    config_path = merged_conf.pop('config-file')
    mount_point = os.path.expanduser(merged_conf['mount-point'])
    merged_conf = read_configuration_file(config_path, mount_point, merged_conf)
    if merged_conf.get('no-input', False):
        validate_missing_information(merged_conf)
    else:
        merged_conf = request_missing_information(merged_conf)

    return merged_conf
