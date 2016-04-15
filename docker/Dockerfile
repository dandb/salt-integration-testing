FROM centos:6

RUN yum install -y epel-release.noarch 

RUN sed -i 's/mirrorlist=https/mirrorlist=http/' /etc/yum.repos.d/epel.repo

RUN rpm --import https://repo.saltstack.com/yum/redhat/6/x86_64/latest/SALTSTACK-GPG-KEY.pub

RUN echo -e "[saltstack-repo]\nname=SaltStack repo for RHEL/CentOS \$releasever\nbaseurl=https://repo.saltstack.com/yum/redhat/\$releasever/\$basearch/latest\nenabled=1\ngpgcheck=1\ngpgkey=https://repo.saltstack.com/yum/redhat/\$releasever/\$basearch/latest/\$releaseverSALTSTACK-GPG-KEY.pub" >> /etc/yum.repos.d/saltstack.repo

RUN yum -y install salt-2015.8.7 salt-minion-2015.8.7

RUN yum -y install python-redis 

ADD minion.conf /etc/salt/minion
ADD setupAndRunHighstate.sh /setupAndRunHighstate.sh

RUN chmod +x /setupAndRunHighstate.sh
CMD ./setupAndRunHighstate.sh

