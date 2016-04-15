#!/bin/bash

if [[ -z $env || -z $master || -z $minion_id || -z $roles ]]; then
    echo -e "missing at least one variable.\n"
    echo -e "You must include all of:\n"
    echo -e "\$env\n\$master\n\$minion_id\n\$roles"
    exit 1
fi

cd /etc/salt

sed -i "s/{{ MASTER }}/$master/g" minion
sed -i "s/{{ ROLES }}/- $roles/" minion
sed -i "s/,/\n    - /g" minion 
sed -i "s/{{ MINION_ID }}/$minion_id/" minion
sed -i "s/{{ ENV }}/$env/" minion

# Since we are modifying the minion config, we need to restart salt
/sbin/service salt-minion restart 

# If somehow the container can't authenticate against the master, we should exit prior to running the highstate
sleep 30
salt-call test.ping >> /dev/null 2>&1
if [[ $( echo $?) -ne 0 ]];then echo "The salt-minion can't authenticate against the master, please investigate. (Failed command: salt-call test.ping)" && exit 2;fi

salt-call -l debug state.highstate --return redis
