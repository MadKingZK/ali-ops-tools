#!/usr/bin/env python3

#import configparser
import hashlib
import json
import math
import os
import pymysql
import time
import sys

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import StopInstanceRequest

PAGESIZE = 100

def Get_node_ip_name(instances_list):
    global NODE_INNER_IP_NAMES
    for instance in instances_list:
        if instance.get("InnerIpAddress").get("IpAddress"):
            inner_ip = instance.get("InnerIpAddress").get("IpAddress")[0]
            instance_name = instance.get("InstanceName")
            if inner_ip not in NODE_INNER_IP_NAMES:
                NODE_INNER_IP_NAMES[inner_ip] = instance_name

def Get_instances(pagenum):
    global NODE_COUNT
    global PAGESIZE
    request.set_PageSize(PAGESIZE)
    request.set_PageNumber(pagenum)
    response = CLIENT.do_action_with_exception(request)
    json_contents = json.loads(response)
    if not NODE_COUNT:
        NODE_COUNT = json_contents.get("TotalCount")

    instances_list = json_contents.get("Instances").get("Instance")
    Get_node_ip_name(instances_list)

def Get_ip_from_zabbix():
    db = pymysql.connect("localhost","root","","zabbix" )
    cursor = db.cursor()
    cursor.execute("select host from hosts")
    data = cursor.fetchone()
    db.close()
    return data

def Notification(dict_ip_name):
    contents = ''
    if dict_ip_name:
        for ip,name in dict_ip_name.items():
            contents = contents + '实例名: ' + name + ', ip: ' + ip + r'\n'
    return contents


if __name__ == "__main__":
    #conf = configparser.ConfigParser()
    #conf.read('ali.ini')
    #accessKeyId = conf.get('client', 'access-key-id')
    #accessKeySecret = conf.get('client', 'accesskeysecret')
    #regionId = conf.get('client', 'regionid')
    accessKeyId = 'ali-key'
    accessKeySecret = 'ali-secret'
    regionId = 'region'
    CLIENT = AcsClient(accessKeyId, accessKeySecret, regionId)
    request = DescribeInstancesRequest.DescribeInstancesRequest()
    # 发起API请求并显示返回值
    request.set_PageSize(1)
    request.set_PageNumber(1)

    response = CLIENT.do_action_with_exception(request)
    json_contents = json.loads(response)
    NODE_COUNT = json_contents.get("TotalCount")

    NODE_INNER_IP_NAMES = {}
    last_page = math.ceil(NODE_COUNT / PAGESIZE) + 1
    for pagenum in range(1, last_page):
        Get_instances(pagenum)
    #print(NODE_INNER_IP_NAMES)
    db = pymysql.connect(user="zabbix",passwd='zabbix',db='zabbix',host='10.10.10.10',charset='utf8')
    cursor = db.cursor()
    cursor.execute("select ip,host from interface, hosts where interface.hostid = hosts.hostid")
    data = cursor.fetchall()
    db.close()
    zabbix_ip_names = {}
    for row in data:
        zabbix_ip_names[row[0]]=row[1]
    lost_ip_name = {}
    for ip,name in NODE_INNER_IP_NAMES.items():
        if ip not in zabbix_ip_names.keys():
            lost_ip_name[ip] = name
    print(Notification(lost_ip_name))
    #print(jsonData)
