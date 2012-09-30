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

It's sufficient to provide mount.s3viewport with a mount point - you will be
prompted for any required information you omit from the command line.


Configuration
-------------

`s3viewport` can be configured in the file `~/.s3viewport.yaml`.
Settings are configured in one of two sections:

* `defaults`, which contains settings that are inherited by all buckets; and
* `mount-points`, which contains a mapping from mount point locations to
  settings for that particular mount point.

Consider the following configuration file:

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
        access-key: ASKJY!*LKASH(*!@LKAS
        secret-key: ASLI*&!@YOILHASD(O*!@U:LA(S*:P!@)N(DS*!(

        file-cache:
            lifetime: 600
            max-bytes: 10M

    ~/mnt/two:
        bucket: bucket-twp
        access-key: ASIU&@#>LSAUP(!@OUPE
```

This configuration file sets up two mount points, `~/mnt/one`, and
`~/mnt/two`:

* `~/mnt/one` configures all of the keys necessary to mount `bucket-one`
  without any input, and overrides the default file cache settings to
  store a maximum of 10 million bytes of files for only 10 minutes each.

* `~/mnt/two` configures only the bucket and access key settings; it will
  require a secret key to be specified in order to mount the bucket.
