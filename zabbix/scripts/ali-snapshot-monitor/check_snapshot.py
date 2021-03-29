#! /usr/bin/env /usr/bin/python3.7
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeDisksRequest, DescribeInstancesRequest
import json

class ecsBandMonitor(object):

    def __init__(self, ali_key, ali_secret, region_id):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )
        # 创建AcsClient实例
        self.client.set_region_id(region_id)

    def getAliyunEcsInfo(self):
        # 获取ecs实例信息，利用迭代器，可直接遍历函数得到ecs实例信息
        # for a in get_aliyun_ecs(ali_key, ali_secret, region_ids):
        #   for ecs in a:
        #       print(ecs['InstanceId'], ecs['HostName'], ecs['ZoneId'], ecs['PublicIpAddress']['IpAddress'], ecs['InnerIpAddress']['IpAddress'], ecs['StartTime'])
        # ecs instance各字段解释：https://help.aliyun.com/document_detail/25656.html?spm=a2c4g.11186623.2.2.a0TLxW#InstanceAttributesType
        # 设置初始页码
        pageNumber = 1

        # 创建request，并设置参数
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(10)
        request.set_PageNumber(pageNumber)
        request.set_InstanceChargeType('PostPaid')
        # request.set_
        response = self.client.do_action_with_exception(request)

        # 发起API请求并显示返回值
        response_dict = json.loads(response)

        # 生成生成器
        while response_dict['Instances']['Instance']:
            yield response_dict['Instances']['Instance']
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

    def checkSnapshotStatus(self):
        pageNumber = 1

        # 创建request，并设置参数
        request = DescribeDisksRequest.DescribeDisksRequest()
        request.set_accept_format('json')
        request.set_PageSize(100)
        request.set_PageNumber(pageNumber)
        # request.set_
        response = self.client.do_action_with_exception(request)

        # 发起API请求并显示返回值
        response_dict = json.loads(response)

        # 生成生成器
        while response_dict['Disks']['Disk']:
            yield response_dict['Disks']['Disk']
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

def main():
    errlst = []
    ecs = ecsBandMonitor('ali-key', 'ali-secret', 'region')
    post_paid_instanceid = []
    for ecs_instances_info in ecs.getAliyunEcsInfo():
        for ecs_info in ecs_instances_info:
             post_paid_instanceid.append(ecs_info.get('InstanceId'))
    for infos in ecs.checkSnapshotStatus():
        for info in infos:
            instance_id = info.get('InstanceId')
            disk_id = info.get('DiskId')
            status = info.get('EnableAutomatedSnapshotPolicy')
            if not status:
                if instance_id not in post_paid_instanceid:
                    errlst.append('磁盘{disk_id}没有添加自动快照策略'.format(instance_id=instance_id, disk_id=disk_id))
    print('\n'.join(errlst))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('调用阿里云接口失败，非运维人员请忽略。')
        print(err)
