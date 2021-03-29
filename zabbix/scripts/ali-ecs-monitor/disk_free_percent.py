#!/usr/bin/env python
import argparse
import os
import psutil

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('dev', type=str, help='disk part name')
parser.add_argument('--type', type=str, default='size', choices=['size', 'inode'], help='default size')
parser.add_argument('--unit', type=str, default='percent', choices=['byte', 'percent'], help='default percent')
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
    if args.unit == 'percent':
        if args.type == 'inode':
            total = float(os.statvfs(diskpart).f_files)
            free = float(os.statvfs(diskpart).f_ffree)
        elif args.type == 'size':
            total =  float(psutil.disk_usage(diskpart).total)
            used  =  float(psutil.disk_usage(diskpart).used)
            free  = total-used
        result = free/total*100
    elif args.unit == 'byte':
        total =  float(psutil.disk_usage(diskpart).total)
        used  =  float(psutil.disk_usage(diskpart).used)
        free  = total-used
        result = free/1024/1024/1024 #unit G
    print("%.2f" % result)
except Exception as e:
    print(e)
