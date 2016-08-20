#!/usr/bin/env python

from troposphere import Template, Ref, Join, autoscaling, cloudformation
from troposphere.ecs import Cluster
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, ScalingPolicy
from troposphere.iam import PolicyType, Role, InstanceProfile
from troposphere.cloudwatch import Alarm, MetricDimension

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
        self.SCALING_METRIC = configs['scaling_metric']
        self.SCALE_UP_THRESHOLD = configs['scale_up_threshold']
        self.SCALE_DOWN_THRESHOLD = configs['scale_down_threshold']
        self.ECS_TASK_CLEANUP_WAIT = configs['ecs_task_cleanup_wait_duration']
        self.template = Template()
        self.user_data = UserData(configs_directory)
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
                            "ecs:Poll",
                            "ecs:StartTelemetrySession",
                            "ecr:GetAuthorizationToken",
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:GetDownloadUrlForLayer",
                            "ecr:BatchGetImage",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*" 
                    }],
                }
            )
        )

        commands = {
            '01_add_instance_to_cluster': {
                'command': Join('', ['#!/bin/bash\n', 'echo ECS_CLUSTER=', Ref(ecs_cluster),
                                     '$"\n"ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=', self.ECS_TASK_CLEANUP_WAIT,
                                     ' >> /etc/ecs/ecs.config'])
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
                UserData=self.user_data.get_base64_data(),
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

        """ Scale UP Policy """
        scaling_up_policy = self.template.add_resource(ScalingPolicy(
            '{0}ScaleUpPolicy'.format(self.AUTOSCALING_GROUP_NAME),
            AdjustmentType='ChangeInCapacity',
            AutoScalingGroupName=Ref(auto_scaling_group),
            Cooldown=60,
            ScalingAdjustment='1'
        ))

        """ Cloud Watch Alarm """
        self.template.add_resource(Alarm(
            '{0}ScaleUpAlarm'.format(self.AUTOSCALING_GROUP_NAME),
            ActionsEnabled=True,
            Namespace='AWS/ECS',
            MetricName=self.SCALING_METRIC,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            Threshold=self.SCALE_UP_THRESHOLD,
            EvaluationPeriods=1,
            Statistic='Average',
            Period=60,
            AlarmActions=[Ref(scaling_up_policy)],
            Dimensions=[
                MetricDimension(
                    Name='ClusterName',
                    Value=Ref(ecs_cluster)
                )
            ]
        ))

        """ Scale DOWN Policy """
        scaling_down_policy = self.template.add_resource(ScalingPolicy(
            '{0}ScaleDownPolicy'.format(self.AUTOSCALING_GROUP_NAME),
            AdjustmentType='ChangeInCapacity',
            AutoScalingGroupName=Ref(auto_scaling_group),
            Cooldown=60,
            ScalingAdjustment='-1'
        ))

        """ Cloud Watch Alarm """
        self.template.add_resource(Alarm(
            '{0}ScaleDownAlarm'.format(self.AUTOSCALING_GROUP_NAME),
            ActionsEnabled=True,
            Namespace='AWS/ECS',
            MetricName=self.SCALING_METRIC,
            ComparisonOperator='LessThanOrEqualToThreshold',
            Threshold=self.SCALE_DOWN_THRESHOLD,
            EvaluationPeriods=1,
            Statistic='Average',
            Period=300,
            AlarmActions=[Ref(scaling_down_policy)],
            Dimensions=[
                MetricDimension(
                    Name='ClusterName',
                    Value=Ref(ecs_cluster)
                )
            ]
        ))

if __name__ == '__main__':
    SITTemplate().print_template()
