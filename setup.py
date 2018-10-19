#!/usr/bin/python

from __future__ import print_function

import os
import sys

import setuptools


py2 = sys.version_info[0] == 2
packages = setuptools.find_packages('src')

extension = '.pyc' if __debug__ else '.pyo'
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()


# Avoid turds left behind during refactorings from affecting new
# test runs.
#
if 'nosetests' in sys.argv[1:]:
    here = os.path.dirname(os.path.abspath(__file__))
    for path, dirs, files in os.walk(here):

        if py2 and path.endswith('/__pycache__'):
            # This directory contains Python 3 bytecode; just ignore it
            # under Python 2.
            continue

        for fn in files:
            if not fn.endswith(extension):
                continue

            if fn.count('.') == 2 and path.endswith('/__pycache__'):
                basename, exectag, extension = fn.split('.')
                pypath = os.path.dirname(path)
                pyfn = os.path.join(pypath, basename + '.py')
            else:
                pypath = path
                pyfn = os.path.join(path, fn[:-1])

            if not os.path.exists(pyfn):
                fn = os.path.join(path, fn)
                print("Removing old bytecode:", fn, file=sys.stderr)
                os.unlink(fn)
                if not os.listdir(path):
                    print("Removing empty folder:", path, file=sys.stderr)
                    os.rmdir(path)
                if path != pypath and not os.listdir(pypath):
                    print("Removing empty folder:", pypath, file=sys.stderr)
                    os.rmdir(pypath)

tests_require = ['nose']
install_requires = [
    'requests',
    'six',
]
if sys.version_info[:2] < (3, 3):
    install_requires.append('mock')

metadata = dict(
    name='kt.testing',
    version='3.1.1',
    description='Test support code featuring flexible harness composition',
    long_description=long_description,
    author='Fred L. Drake, Jr.',
    author_email='fred@fdrake.net',
    url='https://github.com/keepertech/kt.testing',
    packages=packages,
    package_dir={'': 'src'},
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    test_suite='nose.collector',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Testing',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**metadata)
