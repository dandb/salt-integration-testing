import unittest
from troposphere import Base64

from infrastructure.user_data import UserData


class UserDataTest(unittest.TestCase):
    
    def setUp(self):
        self.user_data = UserData()

    def test_get_base64_data(self):
        base_64_data = self.user_data.get_base64_data()
        self.assertEquals(isinstance(base_64_data, Base64), True)
