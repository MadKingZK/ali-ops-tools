#!/bin/bash
if [[ $# -ne 3 ]];then
echo 'args num error'
exit 1
fi
host=$1
db=$2
key=$3
insid=$(echo $host |cut -d'.' -f1)
pwd=$(cat /etc/zabbix/scripts/redis_pwd_cfg.py | grep $insid | sed 's/".*".*"\(.*\)",/\1/g')

if [[ "$pwd"x == x  ]];then
echo 'can not find pwd'
exit 1
fi

res=$(echo "PTTL $key" |redis-cli -h $host -a $pwd -n $db)
echo $res
