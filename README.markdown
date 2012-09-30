s3viewport
==========

Read-only S3 FUSE filesystem based on boto. Useful for viewing logs or other
things that your servers are sending to S3 for safekeeping. Still alpha-quality,
but at least it won't delete your files!

Usage:

    python s3viewport.py <bucket> <mountpoint> <access key> <secret key>
