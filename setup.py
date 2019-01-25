#!/usr/bin/env python

import os
from setuptools import setup
import troposphere

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

def get_cmdclass(needs_install):
    if needs_install:
        return {}
    return {'troposphere': CustomInstall, 'coverage': CustomCoverage}

install_requires = read('requirements.txt').split()
tests_require = read('tests/requirements.txt').split()

needs_install = not os.path.isdir('build')

if not needs_install: 
    from custom_install import CustomInstall
    from custom_coverage import CustomCoverage

setup(
    name="salt-sit",
    version="0.0.3",
    author="Dun and Bradstreet",
    author_email="sit.dandb@gmail.com",
    description=('Salt Integration Testing Tool -- applies role configurations to Docker container minions using AWS (Amazon Web Services) ECS (EC2 Container Service)'),
    license="GPLv3",
    keywords="Salt SaltStack Roles Test Docker AWS EC2 AutoScale AutoScaling Group ECS EC2 Container Service Integration Testing",
    url="https://github.com/dandb/salt-integration-testing",
    packages=['sit'],
    include_package_data=True,
    cmdclass=get_cmdclass(needs_install),
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite="nose.collector",
    long_description=read('README.md') + '\n\n' + read('CHANGES'),
)
