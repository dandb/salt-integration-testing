#!/usr/bin/env python

import os
from custom_install import CustomInstall
from setuptools import setup

install_requires = [
    'boto3',
    'PyYaml',
    'troposphere',
    'redis'
]

tests_require = [
    'placebo',
    'boto3',
    'PyYaml'
]


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name="SIT",
    version="0.0.1",
    author="Dun and Bradstreet",
    author_email="DevOps@dandb.com",
    description=('Salt Integration Testing Tool -- applies role configurations to Docker container minions using AWS (Amazon Web Services) ECS (EC2 Container Service)'),
    license="GPLv3",
    keywords="Salt SaltStack Roles Test Docker AWS EC2 AutoScale AutoScaling Group ECS EC2 Container Service Integration Testing",
    url="https://github.com/dandb/salt-integration-testing",
    packages=['Sit'],
    include_package_data=True,
    cmdclass={'troposphere': CustomInstall},
    install_requires=install_requires,
    tests_require=tests_require,
    long_description=read('README.md') + '\n\n' + read('CHANGES'),
)
