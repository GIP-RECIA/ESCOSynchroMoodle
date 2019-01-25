#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

install_requires = ['mysql-connector-python', 'python-ldap', 'ruamel.yaml']

setup_requires = ['pytest-runner']

dev_require = ['pylint', 'tox']

tests_require = ['pytest']

entry_points = {
    'console_scripts': [
        'synchromoodle = synchromoodle.__main__:main'
    ],
}

with open('synchromoodle/__version__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]$', f.read(), re.MULTILINE).group(1)

args = dict(name='synchromoodle',
            version=version,
            description='Scripts de synchronisation Moodle.',
            # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
            classifiers=['Development Status :: 5 - Production/Stable',
                         'Operating System :: OS Independent',
                         'Programming Language :: Python :: 3',
                         'Programming Language :: Python :: 3.5',
                         'Programming Language :: Python :: 3.6',
                         'Programming Language :: Python :: 3.7'
                         ],
            packages=find_packages(),
            install_requires=install_requires,
            setup_requires=setup_requires,
            tests_require=tests_require,
            entry_points=entry_points,
            test_suite='test',
            zip_safe=True,
            extras_require={
                'test': tests_require,
                'dev': dev_require
            })

setup(**args)
