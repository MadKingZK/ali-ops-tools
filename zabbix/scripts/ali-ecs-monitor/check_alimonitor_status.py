#! /usr/bin/env /usr/bin/python3.7

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstanceStatusRequest
from aliyunsdkcms.request.v20170301 import NodeStatusRequest
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
        request = DescribeInstanceStatusRequest.DescribeInstanceStatusRequest()
        request.set_accept_format('json')
        request.set_PageSize(10)
        request.set_PageNumber(pageNumber)
        # request.set_
        response = self.client.do_action_with_exception(request)

        # 发起API请求并显示返回值
        response_dict = json.loads(response)

        # 生成生成器
        while response_dict['InstanceStatuses']['InstanceStatus']:
            yield response_dict['InstanceStatuses']['InstanceStatus']
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

    def checkAliMonitorStatus(self, instance_id):
        # 实例化request
        request = NodeStatusRequest.NodeStatusRequest()

        # 组装request，接受json
        request.set_accept_format('json')
        request.set_InstanceId(instance_id)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        return response_dict

def main():
    errlst = []
    ecs = ecsBandMonitor('ali-key', 'ali-secret', 'region')
    for infos in ecs.getAliyunEcsInfo():
        for info in infos:
            if info.get('Status') == 'Running':
                instance_id = info.get('InstanceId')
                status_info = ecs.checkAliMonitorStatus(instance_id)
                if status_info.get('Status') != 'running':
                    errlst.append('ecs实例{instance_id}, 监控插件运行异常：{status}'.format(instance_id=instance_id, status=status_info.get('Status')))

    errinfo = '\n'.join(errlst)
    with open('/tmp/alimonitor_status.txt','w') as f:
        f.write(errinfo)

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('调用阿里云接口失败，非运维人员请忽略。')
        with open('/tmp/alimonitor_status.txt','w') as f:
                f.write(errinfo)
        print(err)
