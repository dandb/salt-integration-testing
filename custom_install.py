from setuptools.command.install import install

from infrastructure.sit_loader import SITLoader
from helpers.sit_template_helper import SITTemplateHelper
from helpers.log import Log


class CustomInstall(install):

    def run(self):
        install.run(self)
        Log.setup()
        SITTemplateHelper().validate()
        SITLoader().run()
