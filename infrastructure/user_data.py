#!/usr/bin/env python

from troposphere import Base64, Join, Ref

from helpers.sit_helper import SITHelper


class UserData(object):

    def __init__(self, configs_directory='tests/sit/configs'):
        sit_helper = SITHelper(configs_directory)
        CONFIGS = sit_helper.get_configs('troposphere')
        self.LAUNCH_CONFIGURATION_NAME = CONFIGS['launch_configuration_name']
        self.AUTOSCALING_GROUP_NAME = CONFIGS['autoscaling_group_name']
        self.CUSTOM_USER_DATA = sit_helper.get_custom_user_data()

    def get_base64_data(self):
        cfn_script = Join('', [
            "#!/bin/bash -xe\n",
            '{0}'.format(self.CUSTOM_USER_DATA),
            "yum install -y aws-cfn-bootstrap\n",

            "/opt/aws/bin/cfn-init -v ",
            "         --stack ", Ref("AWS::StackName"),
            "         --resource {0}".format(self.LAUNCH_CONFIGURATION_NAME),
            "         --region ", Ref("AWS::Region"), "\n",

            "/opt/aws/bin/cfn-signal -e $? ",
            "         --stack ", Ref("AWS::StackName"),
            "         --resource {0}".format(self.AUTOSCALING_GROUP_NAME),
            "         --region ", Ref("AWS::Region"), "\n"
        ])
        return Base64(cfn_script)


if __name__ == '__main__':
    print UserData().get_base64_data()
