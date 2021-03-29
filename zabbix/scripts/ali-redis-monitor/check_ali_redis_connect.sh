#!/bin/bash
if [[ $# -lt 3 ]];then
echo 'need more args'
exit 1
fi
host=$1
port=$2
insid=$3
pwd=$(cat /etc/zabbix/scripts/redis_pwd_cfg.py | grep $insid | sed 's/".*".*"\(.*\)",/\1/g')

if [[ "$pwd"x == x  ]];then
echo 'can not find pwd'
exit 1
fi

res=$(redis-cli -h $host -p $port -a $pwd PING)
echo $res
