# Salt Integration Testing (SIT) [![Build Status](https://travis-ci.org/dandb/salt-integration-testing.svg)](https://travis-ci.org/dandb/salt-integration-testing) [![Coverage Status](https://coveralls.io/repos/dandb/salt-integration-testing/badge.svg?branch=master&service=github)](https://coveralls.io/github/dandb/salt-integration-testing?branch=master)

Open source project that allows users to test applying states to roles using AWS ECS (Docker).
Great for integrating within your CI/CD environment!

Technologies used:
* Python2.6/2.7
* Docker
* AWS ECS

## Before we begin

Setting up a CI/CD pipeline is beyond the scope of this README. There are many tools you can use.
The following assumptions are made in utilizing this project:
  1. You are using AWS and your region contains a(n):
    * VPC that houses your CI resources
    * Security group that is used by your CI nodes
    * Subnet that your CI nodes are using
    * Key pair you have access to
    * IAM key credentials with permissions including: AmazonEC2FullAccess and AmazonEC2ContainerServiceFullAccess

## Running SIT
  from root directory of SIT project 
  ```bash
  python -m sit.launch_review_job <job_name> <build_number> <ci_node_private_ip_address>
  ```
  * Job name and build number are used to generate a naming convention for the Docker image minion.
  * Private IP is used by the minion to point to its salt-master, the CI node.
  For this to work, you’ll need to do a few things...

## Let's begin!

  1. Clone the repository
  ```bash
  git clone git@github.com:dandb/salt-integration-testing.git
  ```

  2. Install the project
  ```bash
  python setup.py install
  ```

  3. Set your configs
    1. boto3 AWS credentials
      Time to set a profile. In this example, we are using “sit” as the profile.
      You may use the default profile if you like

      ~/.aws/credentials
      ```python
      [sit]
        aws_access_key_id=<access_key>
        aws_secret_access_key=<secret_key>
      ```
      
      ~/.aws/configs
      ```python
      [profile sit]
        region=<region>
      ```
      If you are using a profile other than default, you will have to change the default inside configs/sit.yml
    2. configs/troposphere.yml

      You will need to find the following values and add them:
      * Security group that your CI instances are using
      * Subnet that your CI instances are provisioned within
      * key pair you have access to
      * Ami_id from: [AWS Marketplace](https://aws.amazon.com/marketplace/search/results/ref=dtl_navgno_search_box?page=1&searchTerms=Amazon+ECS-Optimized+Amazon+Linux+AMI)

  4. Launch the infrastructure
    in root of SIT project:
    ```
    python setup.py troposphere
    ```
    
    Errors, if any, will be shown in the terminal. Once you fix the problems (most likely an error in configs from above steps), re-run this step.

  5. SIT Salt states
  
    You are most likely setting up SIT within a CI/CD environment.
    Your CI nodes will require the SIT repository and your configs. Here are some sample states to help you get set up!

    ```
    {%- set sitdir = '/location/you/want/sit/to/reside/' %}

    {{ sitdir }}:
      file.directory:
        - user: {{ user}}
        - group: {{ user }}
        - dir_mode: 755
        - makedirs: True

    sit:
      git.latest:
        - name: git@github.com:dandb/salt-integration-testing.git
        - rev: master
        - target: {{ sitdir }}
        - force: True
        - require:
        - file: {{ sitdir }}
    ```
 
  6. Configs for SIT
    1. Create a directory called "configs" with these three files:
      * sit.yml
      * troposphere.yml
      * roles.yml
      
      You can copy these files form the SIT repository and edit them as necessary
    2. Replace troposphere.yml with the followowing four variables. 
      You should use private pillar to store sensitive information 
      
      inside: configs/troposphere.yml
      ```python
      security_groups: {{ pillar['sit']['security_group_names'] }}
      key_name: {{ pillar['sit']['key_name'] }}
      ami_id: {{ pillar['sit']['ecs_ami_id'] }}
      subnet: {{ pillar['sit']['subnet'] }}
      ```
      
      configs/roles.yml:

      Add the roles and states you would like to test in this file. A commented out example can be found within the file for guidelines.
      
    3. configs state:
      ```python
      {{ sitdir }}/configs:
      file.recurse:
        - source: salt://location/of/user/generated/sit/configs
        - template: jinja
        - user: {{ user }}
        - group: {{ user }}
        - file_mode: '0755'
        - makedirs: True
        - require:
          - git: sit
      ```
  7. Now you can highstate your CI node(s) with these configurations

## Initiate/Teardown SIT
  You will have to do the following (potentially each build, but depends on your setup) before and after running SIT:
  1. Initiation Script: create an initiation script that will run inside the CI node before any SIT-like job is to be run
    * Edit CI Node's master configs (file_roots and pillar_roots) to point to the workspace of the salt repo. (via SED)
    * Start salt-master on the CI node
    * Start Redis service on the CI node
    * Copy down the roles.yml file from your salt project workspace into the sit configs directory.
    * Install the SIT requirements.

      ```python
      pip install -r /path/to/sit/requirements.txt
      ```


  Once your job is done, you will want the CI node to be able to run other jobs, and even run SIT-like jobs again. This resets the work that the Initiate did.
  2. Teardown script: create a teardown script that will run after SIT tool is done running
    * Delete all keys accepted by salt-master (CI node)
    * Flush Redis of data
    * Stop salt-master service
    * Stop redis
    * Return CI node salt-master configs (file_roots and pillar_roots) to an easy to edit target (via SED)

## Contributing to SIT
  * Please create a pull-request (preferably referring to an issue) with a single, meaningful commit message stating what you are accomplishing.
  * Add unit tests to new code
  * Ensure all unit tests pass and coverage has not dropped
    ```
    python setup.py test
    ```

  * To check coverage, you can run:
    ```
    python setup.py coverage
    ```
