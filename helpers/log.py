#!/usr/bin/env python

import sys
import logging


class Log(object):

    @staticmethod
    def setup(level_logging=logging.INFO):
        logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=level_logging)

    @staticmethod
    def error(message, e=None, exit_code=2):
        logging.error('Message: {0}. Error: {1}. Code: {2}'.format(message, e, exit_code))
        sys.exit(exit_code)

if __name__ == '__main__':
    Log.setup()
