#!/usr/bin/env bash

coverage run --source . setup.py nosetests
coverage html
open htmlcov/index.html
