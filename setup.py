#!/usr/bin/env python

"""
Setup script for the OLC_NAS_Tools package.
"""

# Local imports
from distutils.util import convert_path
import importlib.util
import os
from setuptools import setup, find_packages

# Find the version
version = {}
version_path = convert_path(os.path.join('nastools', 'version.py'))
spec = importlib.util.spec_from_file_location('nastools.version', version_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Adapt to the variable name used in version.py, e.g. __version__ or version
version['__version__'] = getattr(
    mod, '__version__',
    getattr(
        mod,
        'version',
        None
    )
)

setup(
    name="olcnastools",
    version=version['__version__'],
    packages=find_packages(),
    author="Adam Koziol, Andrew Low, Forest Dussault",
    author_email="adam.koziol@inspection.gc.ca",
    url="https://github.com/OLC-Bioinformatics/OLC_NAS_Tools",
    scripts=['nastools/nastools.py']
)
