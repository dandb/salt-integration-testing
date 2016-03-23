from troposphere import Template, Ref, Join, autoscaling, cloudformation
from troposphere.ecs import Cluster
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration 
from troposphere.iam import PolicyType, Role, InstanceProfile  

from UserData import UserData
from helpers.sit_helper import SITHelper

class SITTemplate(object):

    CONFIGS = SITHelper.get_configs('troposphere')
    TEMPLATE_DESCRIPTION = CONFIGS["template_description"]
    INSTANCE_TYPE = CONFIGS["instance_type"]
    SECURITY_GROUPS = CONFIGS["security_groups"]
    KEY_NAME = CONFIGS["key_name"]
    TAG_KEY = CONFIGS["tag_key"]
    TAG_VALUE = CONFIGS["tag_value"]
    AMI_ID = CONFIGS['ami_id']
    MAX_SIZE = CONFIGS['max_size']
    MIN_SIZE = CONFIGS['min_size']
    SUBNET = CONFIGS['subnet']

    def __init__(self):
        self.template = Template()
        self.init_template()

    def print_template(self):
        print self.template.to_json()

    def init_template(self):
        self.template.add_description(self.TEMPLATE_DESCRIPTION)
        
        ecs_cluster = self.template.add_resource(Cluster(
                'sitCluster'
            )
        )

        ecsInstanceRole= self.template.add_resource(Role(
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

        ecsInstanceProfile = self.template.add_resource(InstanceProfile(
                'sitInstanceProfile',
                Path='/',
                Roles=[Ref(ecsInstanceRole)]
            )
        )

        ecsInstancePolicy = self.template.add_resource(PolicyType(
                'sitInstancePolicy',
                PolicyName='ecs-policy',
                Roles=[Ref(ecsInstanceRole)],
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
            "/etc/cfn/cfn-hup.conf" : {
                "content" :  Join("", [
                    "[main]\n",
                    "stack=", Ref("AWS::StackId"), "\n",
                    "region=", Ref("AWS::Region"), "\n"
                ]),
                "mode": "000400",
                "owner": "root",
                "group": "root"
             },
             "/etc/cfn/hooks.d/cfn-auto-reloader.conf" : {
                 "content": Join("", [
                     "[cfn-auto-reloader-hook]\n",
                     "triggers=post.update\n",
                     "path=Resources.sitLaunchConfiguration.Metadata.AWS::CloudFormation::Init\n",
                     "action=/opt/aws/bin/cfn-init -v ",
                     "         --stack ", Ref("AWS::StackName"),
                     "         --resource sitLaunchConfiguration",
                     "         --region ", Ref("AWS::Region"), "\n",
                     "runas=root\n"
                 ])
             }
         }

        services = {
            "sysvinit" : {
                "cfn-hup" : { 
                    "enabled" : "true", 
                    "ensureRunning" : "true", 
                    "files" : [
                        "/etc/cfn/cfn-hup.conf", 
                        "/etc/cfn/hooks.d/cfn-auto-reloader.conf"
                    ]
                }
            }
        }

        launchConfiguration = self.template.add_resource(LaunchConfiguration(
                'sitLaunchConfiguration',
                ImageId=self.AMI_ID,
                IamInstanceProfile=Ref(ecsInstanceProfile),
                InstanceType=self.INSTANCE_TYPE,
                UserData=UserData.get_base64data(),
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

        autoScalingGroup = self.template.add_resource(AutoScalingGroup(
                'sitAutoScalingGroup', 
                MaxSize = self.MAX_SIZE,
                MinSize = self.MIN_SIZE,
                LaunchConfigurationName = Ref(launchConfiguration),
                VPCZoneIdentifier=[self.SUBNET]
            )
        )
        

if __name__ == '__main__':
    print SITTemplate().template.to_json()
