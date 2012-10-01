from distutils.core import setup


requirements = 


setup(name='s3viewport',
      version='20120930',
      description='A FUSE filesystem for viewing S3 buckets',
      author='Brendan MacDonell',
      author_email='brendan@macdonell.net',
      url='https://github.com/bremac/s3viewport',
      packages=['s3viewport'],
      package_dir={'s3viewport': 's3viewport'},
      scripts=['mount.s3viewport'],
      install_requires=[
          'fusepy>=2.0.1',
          'boto>=2.6.0',
          'iso8601>=0.1.4',
          'PyYAML>=3.10',
      ],
      requires=[
          'fusepy (>=2.0.1)',
          'boto (>=2.6.0)',
          'iso8601 (>=0.1.4)',
          'PyYAML (>=3.10)',
      ],
      provides=['s3viewport'])
