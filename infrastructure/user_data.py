#!/usr/bin/env python

from troposphere import Base64, Join, Ref

from helpers.sit_helper import SITHelper


class UserData(object):

    SIT_HELPER = SITHelper()
    CONFIGS = SIT_HELPER.get_configs('troposphere')
    LAUNCH_CONFIGURATION_NAME = CONFIGS['launch_configuration_name']
    AUTOSCALING_GROUP_NAME = CONFIGS['autoscaling_group_name']
    CUSTOM_USER_DATA = SIT_HELPER.get_custom_user_data()

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
