#!/bin/bash

printf "{\n"
printf '\t'"\"data\":["
if [[ -f /etc/supervisor/supervisord.conf ]];then
    printf '\n\t\t{'
    pidfile=$(grep pidfile /etc/supervisor/supervisord.conf |awk -F'=| |;' '{print $2}')
    pid=$(cat $pidfile 2>/dev/null)
    printf "\"{#PROC_NAME}\":\"supervisord\",\"{#PID}\":\"$pid\""
    printf '}'
fi
printf "\n\t]\n"
printf "}\n"
