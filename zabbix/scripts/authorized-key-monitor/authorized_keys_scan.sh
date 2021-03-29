#!/bin/bash
file_array=(`cat /etc/passwd | egrep -v 'nologin|false|sync' | awk -F ':' '{print $6}' | xargs -I {} bash -c 'if [[ -d {} ]];then echo {}; fi'`)
length=${#file_array[@]}
sum=0
printf "{\n"
printf '\t'"\"data\":["
for ((i=0;i<$length;i++))
do
    if [[ -f ${file_array[$i]}/.ssh/authorized_keys ]];then
        if [[ $sum -gt 0 ]];then
            printf ','
        fi
        let sum=sum+1
        printf '\n\t\t{'
        printf "\"{#AUTHKEYFILEPATH}\":\"${file_array[$i]}/.ssh/authorized_keys\"}"
    fi
    if [[ -f ${file_array[$i]}/.ssh/authorized_keys2 ]];then
        if [[ $sum -gt 0 ]];then
            printf ','
        fi
        let sum=sum+1
        printf '\n\t\t{'
        printf "\"{#AUTHKEYFILEPATH}\":\"${file_array[$i]}/.ssh/authorized_keys2\"}"
    fi
done
printf "\n\t]\n"
printf "}\n"
