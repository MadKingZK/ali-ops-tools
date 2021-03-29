#! /usr/bin/env /usr/bin/python3.7
import json
import sys
import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkcms.request.v20170301 import QueryMetricLastRequest


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

    def get_ecs_monitor(self, instances_ids, period):
        # 实例化request
        request = QueryMetricLastRequest.QueryMetricLastRequest()
        # 组装request，接手json，监控流出流量，周期300s
        request.set_accept_format('json')
        request.set_Project('acs_ecs_dashboard')
        request.set_Metric('InternetOutRate')
        request.set_Period(period)
        request.set_Dimensions(instances_ids)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        infos = response_dict.get('Datapoints')
        return infos

def get_json(str):
    str_lst = str.split(',')
    lst = []
    for kv_str in str_lst:
        kv_lst = kv_str.split(':')
        lst.append('"{k}":"{v}"'.format(k=kv_lst[0], v=kv_lst[1]))
    res = '{' + ','.join(lst) + '}'
    return res

def main():
    special_threshold = None
    if len(sys.argv) < 3:
        threshold = None
        period = None
        print('need threshold and period args')
        exit(1)
    else:
        threshold = sys.argv[1]
        period = sys.argv[2]

    try:
        threshold = float(threshold)
        period = int(period)
    except Exception as err:
        print(err)
        print('wrong args type, threshold float, period int')
        exit(2)

    if not 0 < threshold < 1:
        print('wrong arg, needs int, 0 < threshold < 1')
        exit(3)
    elif period % 60 != 0:
        print('wrong second arg, needs int, Multiple of 60')
        exit(4)

    ecs = ecsBandMonitor('ali-key', 'ali-secret', 'region')
    # 测试获取ecs实例信息
    ecs_bandwidth_info = {}
    # 组装instance_ids
    instance_ids = "["
    for ecs_instances_info in ecs.getAliyunEcsInfo():
        for ecs_info in ecs_instances_info:
            if ecs_info.get('InternetMaxBandwidthOut') > 0:
                instance_id = ecs_info.get('InstanceId')
                if special_threshold and instance_id in special_threshold.keys():
                    real_threshold = special_threshold.get(instance_id)
                else:
                    real_threshold = threshold
                ecs_bandwidth_info[ecs_info.get('InstanceId')] = {'instance_name': ecs_info.get('InstanceName'),
                                                                  'public_ipaddress': ecs_info.get('PublicIpAddress'),
                                                                  'max_bandwidth_in': ecs_info.get(
                                                                      'InternetMaxBandwidthIn'),
                                                                  'max_bandwidth_out': ecs_info.get(
                                                                      'InternetMaxBandwidthOut'),
                                                                  'threshold': real_threshold
                                                                  }
                instance_ids += "{'instanceId':'%s'}," % instance_id
    instance_ids += "]"
    bandwidth_infos = ecs.get_ecs_monitor(instance_ids, period)
    # 遍历info 取出instalceid和当前流量值
    result = []
    if os.path.exists('/tmp/ecsBandidthCounter.txt'):
        with open('/tmp/ecsBandidthCounter.txt', 'r') as f:
            counter_dic = json.load(f)
    else:
        counter_dic = {}

    for bandwidth_info in bandwidth_infos:
        instance_id = bandwidth_info.get('instanceId')
        average = round(bandwidth_info.get('Average') / 1024.00 / 1024.00, 2)
        instance_name = ecs_bandwidth_info.get(instance_id).get('instance_name')
        max_bandwidth = ecs_bandwidth_info.get(instance_id).get('max_bandwidth_out')
        if instance_id in counter_dic.keys():
            total_values = counter_dic.get(instance_id)
            total_values.append(average)
            while len(total_values) > 8:
                total_values.pop(0)
        else:
            total_values = []
            total_values.append(average)
        counter_dic[instance_id] = total_values
        if total_values and len(total_values) >= 8:
            total_average = sum(total_values) / len(total_values)
            if total_average > max_bandwidth * threshold:
                result.append(
                    'ECS8小时平均带宽：{instance_name}: {average:.2f} > {threshold_bandwidth:.2f} (max: {max_bandwidth}, units: Mbps)'.format(
                        instance_name=instance_name, average=average,
                        threshold_bandwidth=max_bandwidth * threshold, max_bandwidth=max_bandwidth))

    print('\n'.join(result))
    with open('/tmp/ecsBandidthCounter.txt', 'w') as f:
        json.dump(counter_dic, f)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        exit(1)
