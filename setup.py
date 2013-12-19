#!/usr/bin/env python

from distutils.core import setup

setup(
    name='pymbr',
    version='1.0',
    description='MBR (master boot record) library',
    author='Roy Wellington',
    url='https://github.com/thanatos/pymbr',
    py_modules=['mbr'],
    install_requires=['six'],
)
