#!/usr/bin/env python

from troposphere import Template, Ref, Join, autoscaling, cloudformation
from troposphere.ecs import Cluster
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration 
from troposphere.iam import PolicyType, Role, InstanceProfile  

from user_data import UserData
from helpers.sit_helper import SITHelper


class SITTemplate(object):

    def __init__(self, configs_directory='configs'):
        configs = SITHelper(configs_directory).get_configs('troposphere')
        self.TEMPLATE_DESCRIPTION = configs["template_description"]
        self.INSTANCE_TYPE = configs["instance_type"]
        self.SECURITY_GROUPS = configs["security_groups"]
        self.KEY_NAME = configs["key_name"]
        self.TAG_KEY = configs["tag_key"]
        self.TAG_VALUE = configs["tag_value"]
        self.AMI_ID = configs['ami_id']
        self.MAX_SIZE = configs['max_size']
        self.MIN_SIZE = configs['min_size']
        self.SUBNET = configs['subnet']
        self.CLUSTER_NAME = configs['cluster_name']
        self.AUTOSCALING_GROUP_NAME = configs['autoscaling_group_name']
        self.LAUNCH_CONFIGURATION_NAME = configs['launch_configuration_name']
        self.template = Template()
        self.init_template()

    def print_template(self):
        print self.template.to_json()

    def init_template(self):
        self.template.add_description(self.TEMPLATE_DESCRIPTION)
        
        ecs_cluster = self.template.add_resource(Cluster(
                self.CLUSTER_NAME 
            )
        )

        ecs_instance_role = self.template.add_resource(Role(
                'sitInstanceRole',
                Path='/',
                AssumeRolePolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["ec2.amazonaws.com"]
                        },
                        "Action": ["sts:AssumeRole"]
                    }]
                }
            )
        )

        ecs_instance_profile = self.template.add_resource(InstanceProfile(
                'sitInstanceProfile',
                Path='/',
                Roles=[Ref(ecs_instance_role)]
            )
        )

        ecs_instance_policy = self.template.add_resource(PolicyType(
                'sitInstancePolicy',
                PolicyName='ecs-policy',
                Roles=[Ref(ecs_instance_role)],
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "ecs:CreateCluster",
                            "ecs:RegisterContainerInstance",
                            "ecs:DeregisterContainerInstance",
                            "ecs:DiscoverPollEndpoint",
                            "ecs:Submit*",
                            "ecs:Poll"
                        ],  
                        "Resource": "*" 
                    }],
                }
            )
        )

        commands = {
            '01_add_instance_to_cluster': {
                'command': Join('', ['#!/bin/bash\n', 'echo ECS_CLUSTER=', Ref(ecs_cluster), ' >> /etc/ecs/ecs.config'])
            }   
        }    

        files = {
            "/etc/cfn/cfn-hup.conf": {
                "content" :  Join("", [
                    "[main]\n",
                    "stack=", Ref("AWS::StackId"), "\n",
                    "region=", Ref("AWS::Region"), "\n"
                ]),
                "mode": "000400",
                "owner": "root",
                "group": "root"
            },
            "/etc/cfn/hooks.d/cfn-auto-reloader.conf": {
                "content": Join("", [
                    "[cfn-auto-reloader-hook]\n",
                    "triggers=post.update\n",
                    "path=Resources.{0}.Metadata.AWS::CloudFormation::Init\n".format(self.LAUNCH_CONFIGURATION_NAME),
                    "action=/opt/aws/bin/cfn-init -v ",
                    "         --stack ", Ref("AWS::StackName"),
                    "         --resource {0}".format(self.LAUNCH_CONFIGURATION_NAME),
                    "         --region ", Ref("AWS::Region"), "\n",
                    "runas=root\n"
                ])
             }
         }

        services = {
            "sysvinit": {
                "cfn-hup": {
                    "enabled": "true",
                    "ensureRunning": "true",
                    "files": [
                        "/etc/cfn/cfn-hup.conf", 
                        "/etc/cfn/hooks.d/cfn-auto-reloader.conf"
                    ]
                }
            }
        }

        launch_configuration = self.template.add_resource(LaunchConfiguration(
                self.LAUNCH_CONFIGURATION_NAME, 
                ImageId=self.AMI_ID,
                IamInstanceProfile=Ref(ecs_instance_profile),
                InstanceType=self.INSTANCE_TYPE,
                UserData=UserData().get_base64_data(),
                AssociatePublicIpAddress=True,
                SecurityGroups=self.SECURITY_GROUPS,
                KeyName=self.KEY_NAME,
                Metadata=autoscaling.Metadata(
                    cloudformation.Init({
                        "config": cloudformation.InitConfig(
                            commands=commands,
                            files=files,
                            services=services
                        )
                    })
                )
            )
        )

        auto_scaling_group = self.template.add_resource(AutoScalingGroup(
                self.AUTOSCALING_GROUP_NAME, 
                MaxSize=self.MAX_SIZE,
                MinSize=self.MIN_SIZE,
                LaunchConfigurationName=Ref(launch_configuration),
                VPCZoneIdentifier=[self.SUBNET]
            )
        )
        

if __name__ == '__main__':
    SITTemplate().print_template()
