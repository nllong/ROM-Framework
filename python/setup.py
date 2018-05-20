# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Ambient Loop Metamodels',
    version='0.1.0',
    description='Generate Metamodels for Ambient Loop Analysis from OpenStudio-Server Results',
    long_description=readme,
    author='Nicholas Long',
    author_email='nicholas.l.long@colorado.edu',
    url='https://github.com/nllong/ambient-loop-analysis',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
