#!/bin/bash

Usage(){
    echo "$0 <devname> [type:size|inode] [unit:byte|percent]"
    exit 1
}
dev=$1
shift
while (( $# != 0 ))
do
        case $1 in
            type*)
                checktype=$(echo $1 |cut -d':' -f2)
                shift
                ;;
            unit*)
                unit=$(echo $1 |cut -d':' -f2)
                shift
                ;;
            *)
                shift
                ;;
        esac
done

if [[ $(echo $checktype |grep -wcE 'size|inode') -ne 1 ]];then
    checktype='size'
fi
if [[ $(echo $unit |grep -wcE 'byte|percent') -ne 1 ]];then
    unit='percent'
fi
if [[ "$unit" == 'byte' ]];then
    checktype='size'
fi

#Usage
devchar="/$(echo $dev |sed 's|^/*||')"
devname=$(grep "$devchar " /etc/mtab |awk '{print $1}')

if [[ -z $devname ]];then
    Usage
fi

if [[ "$checktype" == 'size' ]];then
    statline=$(df |grep "^$devname ")
fi
if [[ "$checktype" == 'inode' ]];then
    statline=$(df -i |grep "^$devname ")
fi
total=$(echo $statline |cut -d' ' -f2)
used=$(echo $statline |cut -d' ' -f3)
free=$((total-$used))
if [[ "$unit" == 'byte' ]];then
    result=$(echo "scale=2; $free/1024/1024" |bc)
fi
if [[ "$unit" == "percent" ]];then
    result=$(echo "scale=2; $free*100/$total" |bc)
fi
echo $result
