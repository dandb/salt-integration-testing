#!/usr/bin/env python

from troposphere import Base64, Join, Ref

from helpers.sit_helper import SITHelper


class UserData(object):

    CONFIGS = SITHelper.get_configs('troposphere')
    LAUNCH_CONFIGURATION_NAME = CONFIGS['launch_configuration_name']
    AUTOSCALING_GROUP_NAME = CONFIGS['autoscaling_group_name']

    @classmethod
    def get_base64_data(cls):
        cfn_script = Join('', [
            "#!/bin/bash -xe\n",
            '{0}'.format(SITHelper.get_custom_user_data()),
            "yum install -y aws-cfn-bootstrap\n",

            "/opt/aws/bin/cfn-init -v ",
            "         --stack ", Ref("AWS::StackName"),
            "         --resource {0}".format(cls.LAUNCH_CONFIGURATION_NAME),
            "         --region ", Ref("AWS::Region"), "\n",

            "/opt/aws/bin/cfn-signal -e $? ",
            "         --stack ", Ref("AWS::StackName"),
            "         --resource {0}".format(cls.AUTOSCALING_GROUP_NAME),
            "         --region ", Ref("AWS::Region"), "\n"
        ])
        return Base64(cfn_script)


if __name__ == '__main__':
    print UserData.get_base64_data()
