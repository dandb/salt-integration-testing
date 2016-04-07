#!/usr/bin/env python

import os
from custom_install import CustomInstall
from custom_coverage import CustomCoverage
from setuptools import setup

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

install_requires = [
    read('requirements.txt')
]

tests_require = [
    read('tests/requirements.txt')
]


setup(
    name="SIT",
    version="0.0.1",
    author="Dun and Bradstreet",
    author_email="sit.dandb@gmail.com",
    description=('Salt Integration Testing Tool -- applies role configurations to Docker container minions using AWS (Amazon Web Services) ECS (EC2 Container Service)'),
    license="GPLv3",
    keywords="Salt SaltStack Roles Test Docker AWS EC2 AutoScale AutoScaling Group ECS EC2 Container Service Integration Testing",
    url="https://github.com/dandb/salt-integration-testing",
    packages=['Sit'],
    include_package_data=True,
    cmdclass={'troposphere': CustomInstall, 'coverage': CustomCoverage},
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite="tests/*",
    long_description=read('README.md') + '\n\n' + read('CHANGES'),
)
