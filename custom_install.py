from setuptools.command.install import install
from subprocess import call
import logging

from infrastructure.sit_loader import SITLoader
from helpers.log import Log

class CustomInstall(install):

    def run(self):
        install.run(self)
        Log.setup()
        SITLoader().run()

