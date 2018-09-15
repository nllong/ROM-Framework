# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

print open('rom/rom.py').read()
version = re.search(
    '^__version__\s*=\s*\'(.*)\'',
    open('rom/rom.py').read(),
    re.M).group(1)

setup(
    name='ROM Framework',
    version=version,
    description='Generate Reduced Order Models for Ambient Loop Analysis from OpenStudio-Server Results',
    long_description=readme,
    author='Nicholas Long',
    author_email='nicholas.l.long@colorado.edu',
    url='https://github.com/nllong/ambient-loop-analysis',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
