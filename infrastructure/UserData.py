from troposphere import Base64, Join, Ref

class UserData:

    @staticmethod
    def get_base64data():
        cfn_script = Join('', [
            "#!/bin/bash -xe\n",
            'cat << EOD > /etc/resolv.conf\n',
            'nameserver 10.24.20.40\n',
            'nameserver 172.16.22.25\n',
            'EOD\n',  
             "yum install -y aws-cfn-bootstrap\n",

             "/opt/aws/bin/cfn-init -v ",
             "         --stack ", Ref("AWS::StackName"),
             "         --resource jenkinsSlaveLaunchConfiguration",
             "         --region ", Ref("AWS::Region"), "\n",

             "/opt/aws/bin/cfn-signal -e $? ",
             "         --stack ", Ref("AWS::StackName"),
             "         --resource jenkinsSlaveAutoScaleGroup",
             "         --region ", Ref("AWS::Region"), "\n"
        ])
        return Base64(cfn_script)

