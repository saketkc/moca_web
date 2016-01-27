#!/usr/bin/env python
import os
import re

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, Extension, find_packages
import setuptools.command.build_py
from pip.req import parse_requirements

version_file = os.path.join('src', 'version.py')
fversion = None
metadata = None

with open(version_file, 'r') as f:
   metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", f.read()))

assert metadata is not None
fversion = metadata['version'].split('.')

with open('requirements.txt') as f:
    required = f.read().splitlines()

#required = parse_requirements('requirements.txt')

NAME                  = 'moca'
MAINTAINER            = 'Saket Choudhary'
MAINTAINER_EMAIL      = 'saketkc@gmail.com'
DESCRIPTION           = 'MoCA: A tool for motif conservation analysis'
LICENSE               = 'Simplified BSD'
MAJOR                 = fversion[0]
MINOR                 = fversion[1]
MICRO                 = fversion[2]
ISRELEASED            = False
VERSION               = '%s.%s.%s' % (MAJOR, MINOR, MICRO)
LONG_DESCRIPTION      = open('README.md').read()
URL                   = 'https://github.com/saketkc/moca'
DOWNLOAD_URL                   = 'https://github.com/saketkc/moca'
AUTHOR                = 'Saket Choudhary'
AUTHOR_EMAIL          = 'saketkc@gmail.com'
PLATFORMS             = 'OS Independent'

PACKAGE_DATA          = {'': ['pfm_vertebrates.txt', '*.cfg']
                         }

PACKAGES = find_packages('src')
REQUIRES = required
CLASSIFIERS           = """\
Development Status :: 4 - Beta
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved
Programming Language :: C
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: C++
Topic :: Scientific/Engineering :: Bio-Informatics
Topic :: Scientific/Engineering :: Visualization
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

EXTENSIONS = []
def setup_moca():
    metadata = dict(name=NAME,
                    maintainer=MAINTAINER,
                    maintainer_email=MAINTAINER_EMAIL,
                    description=DESCRIPTION,
                    long_description=LONG_DESCRIPTION,
                    url=URL,
                    download_url=DOWNLOAD_URL,
                    license=LICENSE,
                    classifiers=CLASSIFIERS,
                    author=AUTHOR,
                    author_email=AUTHOR_EMAIL,
                    platforms=PLATFORMS,
                    version=VERSION,
                    packages=PACKAGES,
                    package_data=PACKAGE_DATA,
                    install_requires=REQUIRES,
                    ext_modules=EXTENSIONS,
                    extras_require = {
                        'webserver':  ['flask>=0.10'],
                    },
                    include_package_data = True,
                    package_dir = {'': 'src'},
                    #scripts=['scripts/moca_server', 'scripts/moca_pipeline']
                    )
    setup(**metadata)

if __name__ == '__main__':
    setup_moca()
