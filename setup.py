#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="olcnastools",
    version="1.1.8",
    packages=find_packages(),
    author="Adam Koziol, Andrew Low, Forest Dussault",
    author_email="adam.koziol@canada.ca",
    url="https://github.com/OLC-Bioinformatics/OLC_NAS_Tools",  # link to the repo
    scripts=['nastools/nastools.py'],
    install_requires=['olctools']
)
