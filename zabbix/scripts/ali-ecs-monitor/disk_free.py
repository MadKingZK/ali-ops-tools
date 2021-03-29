#!/usr/bin/env python
import argparse
import psutil

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('dev', type=str,
                    help='disk part name')
args = parser.parse_args()

try:
    mtabfile = open('/etc/mtab', r'ro')
    if args.dev == '/':
        args.dev = ''
    devname = '/' + args.dev + ' '
    for line in mtabfile:
        if devname in line:
            diskpart = line.split(' ')[1]
    mtabfile.close()
    total =  psutil.disk_usage(diskpart).total
    used  =  psutil.disk_usage(diskpart).used
    free  = float(total - used)/1024/1024/1024
    print(free)
except Exception as e:
    print(e)
