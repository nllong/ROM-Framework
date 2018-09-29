# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re

with open('README.rstrst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

version = re.search(
    '^__version__\s*=\s*\'(.*)\'',
    open('rom/version.py').read(),
    re.M).group(1)

setup(
    name='ROM Framework',
    version=version,
    description='Generate Reduced Order Models for Ambient Loop Analysis from OpenStudio-Server Results',
    long_description=readme,
    author='Nicholas Long',
    author_email='nicholas.lee.long@gmail.com',
    url='https://github.com/nllong/ROM-Framework',
    license=license,
    python_requires='>=3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)
