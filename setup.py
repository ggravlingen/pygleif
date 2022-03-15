#!/usr/bin/env python
# -*- coding: utf-8 -*-

# To use a consistent encoding
from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = "3.0.0"
DOWNLOAD_URL = 'https://github.com/ggravlingen/pygleif/archive/{}.zip'.format(VERSION)

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

setup(
    name='pygleif',
    packages=PACKAGES,
    python_requires='>=3.8',
    version=VERSION,
    description='API for LEI',
    long_description=long_description,
    author='ggravlingen',
    author_email='no@email.com',
    url='https://github.com/ggravlingen/pygleif',
    license='MIT',
    keywords='lei-code lei api gleif leicode',
    download_url=DOWNLOAD_URL,
)
