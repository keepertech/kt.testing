#!/usr/bin/python

import os
import sys

import setuptools


packages = setuptools.find_packages('src')

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()


# Avoid turds left behind during refactorings from affecting new
# test runs.
#
if 'nosetests' in sys.argv[1:]:
    here = os.path.dirname(os.path.abspath(__file__))
    for path, dirs, files in os.walk(here):
        for fn in [fn for fn in files
                   if fn.endswith('.pyc') or fn.endswith('.pyo')]:
            if not os.path.exists(fn[:-1]):
                fn = os.path.join(path, fn)
                print 'Removing', fn
                os.unlink(fn)

tests_require = ['nose']

metadata = dict(
    name='kt.testing',
    version='1.1.0',
    description='Test support code featuring flexible harness composition',
    long_description=long_description,
    author='Fred L. Drake, Jr.',
    author_email='fred@fdrake.net',
    url='https://github.com/keepertech/kt.testing',
    packages=packages,
    package_dir={'': 'src'},
    namespace_packages=['kt'],
    install_requires=[
        'mock',
        'requests',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    test_suite='nose.collector',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**metadata)
