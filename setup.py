# -*- coding: utf-8 -*-
"""Packaging logic for Flake8's polyfill."""
import io
import os
import sys

import setuptools

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import flake8_polyfill  # noqa

requires = ['flake8']


def get_long_description():
    """Generate a long description from the README file."""
    descr = []
    for fname in ('README.rst',):
        with io.open(fname, encoding='utf-8') as f:
            descr.append(f.read())
    return '\n\n'.join(descr)


setuptools.setup(
    name='flake8-polyfill',
    license='MIT',
    version=flake8_polyfill.__version__,
    description='Polyfill package for Flake8 plugins',
    long_description=get_long_description(),
    author='Ian Cordasco',
    author_email='graffatcolmingov@gmail.com',
    url='https://gitlab.com/pycqa/flake8',
    package_dir={'': 'src'},
    packages=[
        'flake8_polyfill',
    ],
    install_requires=requires,
    classifiers=[
        "Environment :: Console",
        "Framework :: Flake8",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
