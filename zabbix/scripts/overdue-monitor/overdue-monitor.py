#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Introduce : 监控阿里云服务过期，因为阿里云默认剩余9天就会自动续费，所以判断依据是剩余8天内过期的服务或ecs就需要报警
@File      : overdue-monitor.py
@Time      : 2021/3/29 16:31
@Author    : MadKingZK
@Emile     : harvey_dent@163.com
@pip       : pip install 
"""
import argparse

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest as ecsDescribeInstancesRequest
from aliyunsdkr_kvstore.request.v20150101 import DescribeInstancesRequest as redisDescribeInstancesRequest

import json, time, sys


class AliApiTools(object):

    def __init__(self, ali_key, ali_secret):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )

    def getAliyunEcsInfo(self, region_ids):
        """
        获取ecs实例信息，利用迭代器，可直接遍历函数得到ecs实例信息
        调用方法
        for a in get_aliyun_ecs(ali_key, ali_secret, region_ids):
           for ecs in a:
               print(ecs['InstanceId'], ecs['HostName'], ecs['ZoneId'], ecs['PublicIpAddress']['IpAddress'], ecs['InnerIpAddress']['IpAddress'], ecs['StartTime'])
        ecs instance各字段解释：https://help.aliyun.com/document_detail/25656.html?spm=a2c4g.11186623.2.2.a0TLxW#InstanceAttributesType
        """

        # 创建AcsClient实例
        for region_id in region_ids:

            self.client.set_region_id(region_id)

            # 设置初始页码
            pageNumber = 1

            # 创建request，并设置参数
            request = ecsDescribeInstancesRequest.DescribeInstancesRequest()
            request.set_accept_format('json')
            request.set_PageSize(10)
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)

            # 发起API请求并显示返回值
            response_dict = json.loads(response.decode('utf-8'))

            # 生成生成器
            while response_dict['Instances']['Instance']:
                yield response_dict['Instances']['Instance']
                pageNumber += 1
                request.set_PageNumber(pageNumber)
                response = self.client.do_action_with_exception(request)
                response_dict = json.loads(response.decode('utf-8'))

    def getAliyunRedisInfo(self, region_ids):
        for region_id in region_ids:

            self.client.set_region_id(region_id)
            # 设置初始页码
            pageNumber = 1

            # 创建request，并设置参数
            request = redisDescribeInstancesRequest.DescribeInstancesRequest()
            request.set_accept_format('json')
            request.set_PageSize(10)
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)

            # 发起API请求并显示返回值
            response_dict = json.loads(response.decode('utf-8'))

            # 生成生成器
            while response_dict['Instances']['KVStoreInstance']:
                yield response_dict['Instances']['KVStoreInstance']
                pageNumber += 1
                request.set_PageNumber(pageNumber)
                response = self.client.do_action_with_exception(request)
                response_dict = json.loads(response.decode('utf-8'))

    def get_ecs_overdue_sum(self, region):
        # 获取ecs实例即将过期个数（14天）
        overdue_ecs_sum = 0
        for ecs_instances_info in client.getAliyunEcsInfo([region]):
            for ecs_info in ecs_instances_info:
                expired_time_str = ecs_info['ExpiredTime']
                expired_date = int(time.mktime(time.strptime(expired_time_str, "%Y-%m-%dT%H:%MZ")))
                remain_time = expired_date - int(time.time())
                if remain_time < 691200:
                    overdue_ecs_sum += 1

        return overdue_ecs_sum

    def get_redis_overdue_sum(self, region):
        # 获取redis实例即将过期个数（14天）
        overdue_redis_sum = 0
        for redis_instances_info in client.getAliyunRedisInfo([region]):
            for redis_info in redis_instances_info:
                expired_time_str = redis_info['EndTime']
                expired_date = int(time.mktime(time.strptime(expired_time_str, "%Y-%m-%dT%H:%M:%SZ")))
                remain_time = expired_date - int(time.time())
                if remain_time < 691200:
                    overdue_redis_sum += 1

        return overdue_redis_sum

    @staticmethod
    def parse_args():
        # 解析参数
        parser = argparse.ArgumentParser(description="monitor overdue from aliyun")
        parser.add_argument(
            "-t",
            "--servertype",
            type=str,
            choices=["redis", "ecs"],
            required=True,
            help="阿里云服务类型",
        )
        parser.add_argument(
            "-r",
            "--region",
            type=str,
            required=True,
            help="阿里云服务或ecs所在可用区，例如region",
        )

        args = parser.parse_args()
        return args


if __name__ == '__main__':
    args = AliApiTools.parse_args()

    client = AliApiTools('ali-key', 'ali-secret')

    if args.servertype == 'ecs':
        print(client.get_ecs_overdue_sum(args.region))
    elif args.servertype == 'redis':
        print(client.get_redis_overdue_sum(args.region))
