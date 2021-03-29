#!/bin/bash
diskarray=(`cat /proc/diskstats | grep -E "\bvd[a-z]\b|\bxvd[a-z]\b"|grep -i "\b$1\b"|awk '{print $3}'|sort|uniq 2>/dev/null`)
length=${#diskarray[@]}
patharray=()
for ((i=0;i<$length;i++))
do
    name=$(grep ${diskarray[$i]} /etc/mtab | grep -v '/var/lib/docker' |awk '{print $2}' |head -n1)
# |awk -F'/' '{print $NF}')
    if [[ "x$name" == "x" ]];then
        name='/'
    fi
    if [[ $(echo ${patharray[@]} |grep -wc $name) -eq 0 ]] ;then
        patharray[${#patharray[@]}]=$name
    fi
done

printf "{\n"
printf '\t'"\"data\":["
for ((i=0;i<$length;i++))
do
    printf '\n\t\t{'
    printf "\"{#DISKNAME}\":\"${patharray[$i]}\"}"
    if [ $i -lt $[$length-1] ];then
        printf ','
    fi
done
printf "\n\t]\n"
printf "}\n"
