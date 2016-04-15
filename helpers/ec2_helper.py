#!/usr/bin/env python

import logging
from boto3.session import Session

from helpers.sit_helper import SITHelper


class EC2Helper(object):

    def __init__(self, configs_directory='configs', session=None):
        if session is None:
            sit_configs = SITHelper(configs_directory).get_configs('sit')
            session = Session(profile_name=sit_configs['profile_name'])
        self.ec2_client = session.client('ec2')

    def describe_key_pairs(self, key_names):
        try:
            return self.ec2_client.describe_key_pairs(KeyNames=key_names)
        except Exception as e:
            logging.info(e)
            return False

    def describe_images(self, images):
        try:
            return self.ec2_client.describe_images(ImageIds=images)
        except Exception as e:
            logging.info(e)
            return False

    def describe_security_groups(self, security_groups):
        try:
            return self.ec2_client.describe_security_groups(GroupIds=security_groups)
        except Exception as e:
            logging.info(e)
            return False

    def describe_subnets(self, subnets):
        try:
            return self.ec2_client.describe_subnets(SubnetIds=subnets)
        except Exception as e:
            logging.info(e)
            return False
