import unittest

from helpers.sit_helper import SITHelper


class SitHelperTest(unittest.TestCase):

    def setUp(self):
        self.sit_helper = SITHelper('tests/helpers/configs')
        self.sit_helper_empty = SITHelper('tests/helpers/empty_configs')

    def test_get_custom_user_data(self):
        self.assertEquals(self.sit_helper.get_custom_user_data(), "'test'\n")

    def test_get_roles(self):
        self.assertEquals(self.sit_helper.get_roles(), ['lb', 'php'])
        self.assertEquals(self.sit_helper.get_roles(), ['lb', 'php'])
        self.assertEquals(self.sit_helper_empty.get_roles(), False)

    def test_get_states_for_role(self):
        self.assertEquals(self.sit_helper.get_states_for_role('php'), ['apache', 'server'])
        self.assertEquals(self.sit_helper.get_states_for_role('lb'), ['lb', 'server'])
        self.assertEquals(self.sit_helper.get_states_for_role('saltmaster'),
                          "Failed to find state list for role: saltmaster. error: 'saltmaster'")

    def test_get_configs(self):
        self.assertEquals(self.sit_helper.get_configs('roles'), {'lb': {'priority': 1, 'subroles': ['lb', 'server']},
                                                                 'php': {'priority': 2, 'subroles': ['apache', 'server']}})
