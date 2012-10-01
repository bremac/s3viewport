from collections import deque
from datetime import datetime, timedelta
import errno
import os
import os.path
import posixpath
import stat
import tempfile
import threading
import time
import iso8601

import boto.s3.prefix
from boto.s3.connection import S3Connection
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import s3viewport.config
from s3viewport.utils import filter_dict, parse_value_with_si_suffix


class BasePathCache(object):
    class Entry(object):
        def __init__(self, path):
            self.path = path
            self.timestamp = datetime.now()

    def __init__(self, conf):
        self.lifetime = timedelta(seconds=conf['lifetime'])
        self.cache = {}

    def add(self, path, *args, **kwargs):
        entry = self.Entry(path, *args, **kwargs)
        self.cache[path] = entry

    def __contains__(self, path):
        return path in self.cache

    def __getitem__(self, path):
        raise NotImplemented()

    def get(self, path, default=None):
        if not path in self:
            return default
        else:
            return self[path]

    def expire(self):
        now = datetime.now()
        self.cache = filter_dict(
            self.cache, lambda k, v: v.timestamp + self.lifetime >= now)

    def purge(self):
        self.cache = {}


class S3AttributeCache(BasePathCache):
    """

    """

    class Entry(BasePathCache.Entry):
        def __init__(self, path, mode, key=None):
            super(S3AttributeCache.Entry, self).__init__(path)
            self.mode = mode

            if key is not None:
                last_modified = iso8601.parse_date(key.last_modified)
                self.size = key.size
            else:
                last_modified = datetime.now()
                self.size = 0

            self.last_modified = time.mktime(last_modified.timetuple())

    def __init__(self, conf):
        super(S3AttributeCache, self).__init__(conf)

    def __getitem__(self, path):
        return self.cache[path]


class S3DirectoryCache(BasePathCache):
    """

    """

    class Entry(BasePathCache.Entry):
        def __init__(self, path, children):
            super(S3DirectoryCache.Entry, self).__init__(path)
            self.children = children

    def __init__(self, conf):
        super(S3DirectoryCache, self).__init__(conf)

    def __getitem__(self, path):
        return self.cache[path].children


class S3FileCache(BasePathCache):
    """

    """

    class Entry(BasePathCache.Entry):
        def __init__(self, path, path_in_cache, size):
            super(S3FileCache.Entry, self).__init__(path)
            self.path_in_cache = path_in_cache
            self.size = size

    def __init__(self, conf):
        super(S3FileCache, self).__init__(conf)

        self.maximum_size_bytes = parse_value_with_si_suffix(conf['max-bytes'])
        self.maximum_files = conf['max-files']

        self.files_by_path = {}
        self.files_lru = deque()
        self.file_size_bytes = 0

    def _delete_file_from_cache(self, entry):
        try:
            self.files_lru.remove(entry)
        except ValueError:
            pass

        self.files_by_path.pop(entry.path)
        self.file_size_bytes -= entry.size
        os.remove(entry.path_in_cache)

    def add(self, path, path_in_cache, size):
        # Make sure that our byte count and the lru cache don't get out of sync
        if path in self.files_by_path:
            self._delete_file_from_cache(self.files_by_path[path])

        entry = S3FileCache.Entry(path, path_in_cache, size)
        self.files_by_path[path] = entry
        self.files_lru.append(entry)
        self.maximum_size_bytes += size

    def __contains__(self, path):
        return path in self.files_by_path

    def __getitem__(self, path):
        return self.files_by_path[path].path_in_cache

    def _pop_one_file_from_cache(self):
        entry = self.files_lru.popleft()
        self._delete_file_from_cache(entry)

    def expire(self):
        now = datetime.now()
        while (len(self.files_lru) > 0 and
               self.files_lru[0].timestamp + self.lifetime < now):
            self._pop_one_file_from_cache()

    def compact(self):
        while (len(self.files_lru) > self.maximum_files or
               self.file_size_bytes > self.maximum_size_bytes):
            self._pop_one_file_from_cache()

    def purge(self):
        while len(self.files_by_path) > 0:
            self._pop_one_file_from_cache()


def key_basename(key):
    name = key.name.encode('utf-8')
    return name.strip('/').split('/')[-1]


class S3Viewport(LoggingMixIn, Operations):
    """

    """

    FILE_MODE = stat.S_IFREG | 0600
    DIRECTORY_MODE = stat.S_IFDIR | 0700

    def __init__(self, conf):
        connection = S3Connection(conf['access-key'], conf['secret-key'])
        self.bucket = connection.lookup(conf['bucket'])
        self._lock = threading.RLock()
        self.attribute_cache = S3AttributeCache(conf['attribute-cache'])
        self.file_cache = S3FileCache(conf['file-cache'])
        self.directory_cache = S3DirectoryCache(conf['directory-cache'])

        self.gid = os.getgid()
        self.uid = os.getuid()

        cache_path = "~/.s3viewport/cache/{0}".format(self.bucket.name)
        self.cache_path = os.path.expanduser(cache_path)

        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def destroy(self, private_data):
        with self._lock:
            self.attribute_cache.purge()
            self.directory_cache.purge()
            self.file_cache.purge()

    def _fetch_file_from_cache(self, path):
        self.file_cache.expire()

        if path not in self.file_cache:
            self.file_cache.compact()

            key = self.bucket.get_key(path)
            handle, path_in_cache = tempfile.mkstemp(dir=self.cache_path)
            key.get_contents_to_filename(path_in_cache)
            os.close(handle)

            self.file_cache.add(path, path_in_cache, key.size)

        path_in_cache = self.file_cache.get(path)
        return path_in_cache

    def read(self, path, size, offset, fh=None):
        with self._lock:
            path_in_cache = self._fetch_file_from_cache(path)

            if path_in_cache is None:
                raise FuseOSError(errno.ENOENT)

            with open(path_in_cache, 'rb') as f:
                f.seek(offset, 0)
                return f.read(size)

    def _fetch_directory_from_cache(self, path):
        self.directory_cache.expire()

        if path not in self.directory_cache:
            s3_path = '{0}/'.format(path.rstrip('/')).lstrip('/')
            child_keys = self.bucket.list(prefix=s3_path, delimiter='/')

            # Add the child keys to the directory cache
            children = [ key_basename(k) for k in child_keys ]
            self.directory_cache.add(path, children)

            # Add the child keys to the attribute cache
            for key in child_keys:
                is_directory = isinstance(key, boto.s3.prefix.Prefix)
                child_path = '/{0}'.format(key.name).rstrip('/')

                if is_directory:
                    mode = self.DIRECTORY_MODE
                    self.attribute_cache.add(child_path, mode)
                else:
                    mode = self.FILE_MODE
                    self.attribute_cache.add(child_path, mode, key)

        children = self.directory_cache.get(path)
        return children

    def readdir(self, path, fh=None):
        with self._lock:
            children = self._fetch_directory_from_cache(path)

        if children is None:
            raise FuseOSError(errno.ENOENT)
        else:
            return ['.', '..'] + children

    def getattr(self, path, fh=None):
        # We can't retrieve any info for the non-existent root directory
        if path == '/':
            return { 'st_mode': self.DIRECTORY_MODE }

        with self._lock:
            self.attribute_cache.expire()

            if not path in self.attribute_cache:
                # Fetch the parent directory to fill the cache
                self.readdir(posixpath.dirname(path))

            attributes = self.attribute_cache.get(path, None)

            if attributes is None:
                raise FuseOSError(errno.ENOENT)

        return {
            'st_mode': attributes.mode,
            'st_mtime': attributes.last_modified,
            'st_size': attributes.size,
            'st_gid': self.gid,
            'st_uid': self.uid,
        }


def run():
    conf = s3viewport.config.get_configuration()
    fs = s3viewport.filesystem.S3Viewport(conf)
    fuse = FUSE(fs,
                conf['mount-point'],
                foreground=conf['foreground'],
                nothreads=True)


if __name__ == '__main__':
    run()
