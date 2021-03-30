#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Introduce : 给不同类型服务的磁盘，批量绑定不同的快照规则
@File      : set_snaprule.py
@Time      : 2021/3/29 10:35
@Author    : MadKingZK
@Emile     : harvey_dent@163.com
@pip       : pip install alibabacloud_ecs20140526==2.0.2
"""

import argparse
import asyncio
import csv

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models


# 阿里云磁盘快照工具类
class DiskSnapTools:
    def __init__(self, access_key_id, access_key_secret, region):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region = region
        # self.endpoint = 'ecs-' + region + '.aliyuncs.com'
        self.client = self.create_client()

    # 创建client
    def create_client(self) -> Ecs20140526Client:
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=self.access_key_id,
            # 您的AccessKey Secret,
            access_key_secret=self.access_key_secret
        )
        # 访问的域名
        config.region_id = self.region
        return Ecs20140526Client(config)

    # 根据实例id获取磁盘信息
    async def get_disk_info_async(self, instance_id) -> None:
        describe_disks_request = ecs_20140526_models.DescribeDisksRequest(
            region_id=self.region,
            instance_id=instance_id,
        )
        # 调用阿里云接口，请求磁盘信息
        result = await self.client.describe_disks_async(describe_disks_request)
        return result

    def get_dbs_disks_info(self, instance_id, instance_name):
        if instance_name.endswith('-0') or instance_name.endswith('-1'):
            result = asyncio.run(self.get_disk_info_async(instance_id))
            disks_info = (result.to_map().get('body').get('Disks').get('Disk'))

            for disk in disks_info:
                disk_id = disk.get('DiskId')
                snapshot_id = disk.get('AutoSnapshotPolicyId')
                yield (disk_id, snapshot_id)

    def get_pika_disks_info(self, instance_id, instance_name):
        if instance_name.endswith('-0') or instance_name.endswith('-1'):
            result = asyncio.run(self.get_disk_info_async(instance_id))
            disks_info = (result.to_map().get('body').get('Disks').get('Disk'))
            for disk in disks_info:
                disk_id = disk.get('DiskId')
                snapshot_id = disk.get('AutoSnapshotPolicyId')
                yield (disk_id, snapshot_id)

    @staticmethod
    def csv_reader(csv_file):
        csv_reader = csv.reader(open(csv_file))
        for row in csv_reader:
            instance_id = row[0]
            instance_name = row[1]
            yield (instance_id, instance_name)

    # 设置磁盘快照规则
    async def set_snanp(self, snap_id, disk_ids):
        apply_auto_snapshot_policy_request = ecs_20140526_models.ApplyAutoSnapshotPolicyRequest(
            region_id=self.region,
            auto_snapshot_policy_id=snap_id,
            disk_ids=disk_ids,
        )
        # 调用阿里云接口，设置磁盘快照规则
        result = await self.client.apply_auto_snapshot_policy_async(apply_auto_snapshot_policy_request)
        return result

    # 过滤出快照规则有误或为空的磁盘，调用set_snanp方法设置上快照规则
    def set_nosnap_rule_disk(self, disk_id, snapshot_id, correct_snapid, service_type):
        if snapshot_id != correct_snapid:
            disk_ids = "['" + disk_id + "']"
            try:
                set_snap_res = asyncio.run(self.set_snanp(correct_snapid, disk_ids))
                print(set_snap_res.to_map)
            except Exception as err:
                print("-->", disk_id, err)

    # 工具入口
    def run(self, service_type, csv_file, correct_snapid):
        if service_type == "db":
            for instance_id, instance_name in self.csv_reader(csv_file):
                for disk_id, snapshot_id in self.get_dbs_disks_info(instance_id, instance_name):
                    self.set_nosnap_rule_disk(disk_id, snapshot_id, correct_snapid, service_type)

        if service_type == "pika":
            for instance_id, instance_name in self.csv_reader(csv_file):
                for disk_id, snapshot_id in self.get_dbs_disks_info(instance_id, instance_name):
                    self.set_nosnap_rule_disk(disk_id, snapshot_id, correct_snapid, service_type)






if __name__ == '__main__':
    # 解析参数
    parser = argparse.ArgumentParser(description="set snapshot rule args")
    parser.add_argument(
        "-r",
        "--ruleid",
        type=str,
        required=True,
        help="快照规则id",
    )
    parser.add_argument(
        "-f",
        "--csvfile",
        type=str,
        required=True,
        help="实例信息csv文件，【instance_id, instance_name】",
    )

    parser.add_argument(
        "-t",
        "--servicetype",
        type=str,
        choices=["redis", "db", "php", "go"],
        required=True,
        help="服务类型，根据不同的服务设置不同的快照规则",
    )
    args = parser.parse_args()

    disk_snap_tools = DiskSnapTools('ali-key', 'ali-secret', 'ali-region')
    disk_snap_tools.run(args.servicetype, args.csvfile, args.ruleid)