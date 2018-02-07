#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = "0.1.3"
DOWNLOAD_URL = \
    'https://github.com/ggravlingen/pygleif/archive/{}.zip'.format(VERSION)

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

setup(
  name='pygleif',
  packages=PACKAGES,
  python_requires='>=3.4',
  version=VERSION,
  description='API for LEI',
  long_description=long_description,
  author='ggravlingen',
  author_email='no@email.com',
  url='https://github.com/pygleif',
  license='MIT',
  keywords='lei-code lei api gleif',
  download_url=DOWNLOAD_URL
)
