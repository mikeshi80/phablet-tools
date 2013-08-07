#!/usr/bin/python

from setuptools import find_packages
from setuptools import setup

setup(
    name='phablet-tools',
    version='0.1',
    description='Scripts to deploy Ubuntu on mobile devices',
    author='Sergio Schvezov',
    author_email='sergio.schvezov@canonical.com',
    license='GPLv3',
    packages=find_packages(exclude=("tests",)),
    scripts=['phablet-flash',
             'phablet-demo-setup',
             'phablet-network-setup',
             'phablet-dev-bootstrap',
             'phablet-test-run',
             'repo',
            ],
    test_suite='tests',
)
