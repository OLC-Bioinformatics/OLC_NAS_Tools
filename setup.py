#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="olcnastools",
    version="1.1.7",
    packages=find_packages(),
    author="Adam Koziol, Forest Dussault",
    author_email="adam.koziol@canada.ca",
    url="https://github.com/OLC-Bioinformatics/OLC_NAS_Tools",  # link to the repo
    scripts=['nastools/nastools.py'],
    install_requires=['olctools']
)
