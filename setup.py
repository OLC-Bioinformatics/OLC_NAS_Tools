#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="olcnastools",
    version="1.2.5",
    packages=find_packages(),
    author="Adam Koziol, Andrew Low, Forest Dussault",
    author_email="adam.koziol@inspection.gc.ca",
    url="https://github.com/OLC-Bioinformatics/OLC_NAS_Tools",
    entry_points={
        'console_scripts': [
            'nastools.py = nastools.nastools:main'
        ]
    },
)
