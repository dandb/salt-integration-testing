import unittest
from nose.tools import raises

from helpers.log import Log


class EC2HelperTest(unittest.TestCase):
    
    def test_setup(self):
        log = Log.setup()

    @raises(SystemExit)
    def test_error(self):
        self.assertRaises(SystemExit, Log.error(2))



