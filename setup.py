#!/usr/bin/env python

import os

try:
    import setuptools
except ImportError:
    print ('Not found')
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup

ver_file = os.path.join('bottleneck', 'version.py')
