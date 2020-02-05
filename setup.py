#!/usr/bin/python

from __future__ import print_function

import os
import sys

import setuptools


py2 = sys.version_info[0] == 2
packages = setuptools.find_packages('src')

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

install_requires = [
    'requests',
    'six',
]
if sys.version_info[:2] < (3, 3):
    install_requires.append('mock')

metadata = dict(
    name='kt.testing',
    version='0',
    description='Test support code featuring flexible harness composition',
    long_description=long_description,
    author='Fred L. Drake, Jr.',
    author_email='fred@fdrake.net',
    url='https://github.com/keepertech/kt.testing',
    packages=packages,
    package_dir={'': 'src'},
    install_requires=install_requires,
    extras_require={
        'test': [],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Testing',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**metadata)
