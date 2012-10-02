s3viewport
==========

Read-only S3 FUSE filesystem based on boto. Useful for viewing logs or other
things that your servers are sending to S3 for safekeeping. Still alpha-quality,
but at least it won't delete your files!


Basic Usage
-----------

```bash
mount.s3viewport <mountpoint> [--bucket NAME] [--access-key AKEY] [--secret-key SKEY]

# ... do something with <mountpoint> ...

fusermount -u <mountpoint>
```

If you omit any required credentials, `s3viewport` will prompt you to enter
them. For more information on command-line parameters, see
`mount.s3viewport --help`.


Configuration
-------------

`s3viewport` can be configured in the file `~/.s3viewport.yaml`. Settings can
be specified in two sections:

* `defaults`, which contains settings that are inherited by all buckets; and
* `mount-points`, which contains a mapping from mount point locations to
  settings for that particular mount point.

Each section can set the following values, where `a.b` represents the value
`b` in a subsection `a`:

* `attribute-cache.lifetime:` the number of seconds to keep file metadata
  cached after retrieval
* `directory-cache.lifetime:` number of seconds to keep directory listings
  cached after retrieval
* `file-cache.lifetime:` number of seconds to keep files cached after
  retrieval
* `file-cache.max-bytes:` maximum total bytes that the file cache may
  occupy. May be written as 10M, 4K, etc.
* `file-cache.max-files:` maximum number of files to keep in the cache
* `bucket:` name of the S3 bucket to mount
* `access-key:` access key to use to mount the S3 bucket
* `secret-key:` secret key to use to mount the S3 bucket
* `foreground:` true if `s3viewport` should not daemonize itself, false
   otherwise
* `no-input:` true if `s3viewport` should not prompt for missing S3
   credentials, false otherwise

As an example, consider the following configuration file:

```yaml
defaults:
    attribute-cache:
        lifetime: 3600

    directory-cache:
        lifetime: 120

    file-cache:
        lifetime: 3600
        max-files: 1000
        max-bytes: 100M

mount-points:
    ~/mnt/one:
        bucket: bucket-one
        access-key: ASIUSDKJADAHS52SKJSA
        secret-key: ASLI7N/YOILHASD9O000UASAFSQEPJGLNMDMMBDE

        file-cache:
            lifetime: 600
            max-bytes: 10M

    ~/mnt/two:
        bucket: bucket-two
        access-key: ASM923K9DKL92JUIAM23
```

This configuration file sets up two mount points, `~/mnt/one`, and
`~/mnt/two`:

* `~/mnt/one` specifies all of the info necessary to mount `bucket-one`
  without any input from the user, and overrides the default file cache
  settings to store a maximum of 10 million bytes of files for only 10
  minutes each.

* `~/mnt/two` configures only the bucket and access key settings; it will
  require a secret key to be specified in order to mount the bucket.

Of course, the most configurations will be much simpler. If you want to
mount a few buckets that all share the same credentials, the following
would suffice:

```yaml

defaults:
    access-key: ASIUSDKJADAHS52SKJSA
    secret-key: ASLI7N/YOILHASD9O000UASAFSQEPJGLNMDMMBDE

mount-points:
    ~/mnt/one:
        bucket: bucket-one

    ~/mnt/two:
        bucket: bucket-two
```
