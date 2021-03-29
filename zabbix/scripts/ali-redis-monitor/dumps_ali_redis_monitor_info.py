#! /usr/bin/env /usr/bin/python3.7
from aliyunsdkcore.client import AcsClient
from aliyunsdkr_kvstore.request.v20150101 import DescribeInstancesRequest
from aliyunsdkcms.request.v20170301 import QueryMetricLastRequest
import json
import sys


class aliRedisMonitor(object):

    def __init__(self, ali_key, ali_secret, region_id):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )
        # 创建AcsClient实例
        self.client.set_region_id(region_id)

    def get_aliredis_instanceid(self, regionids):
        for regionid in regionids:
            self.client.set_region_id(regionid)
            # 设置初始页码
            pageNumber = 1

            request = DescribeInstancesRequest.DescribeInstancesRequest()
            request.set_accept_format('json')
            request.set_PageSize(10)
            request.set_PageNumber(pageNumber)

            # 发起API请求并显示返回值
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

            # 生成生成器
            while response_dict['Instances']['KVStoreInstance']:
                yield response_dict['Instances']['KVStoreInstance']
                pageNumber += 1
                request.set_PageNumber(pageNumber)
                response = self.client.do_action_with_exception(request)
                response_dict = json.loads(response)

    def get_ali_monitor_info(self, instances_ids, metric, period):
        # 实例化request
        request = QueryMetricLastRequest.QueryMetricLastRequest()
        # 组装request，接手json，监控流出流量，周期300s
        request.set_accept_format('json')
        request.set_Project('acs_kvstore')
        request.set_Metric(metric)
        request.set_Period(period)
        request.set_Dimensions(instances_ids)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        infos = response_dict.get('Datapoints')
        return infos


def get_instances():
    instance_infos = {}
    acs = aliRedisMonitor('ali-key', 'ali-secret', 'region')
    for redis_instances in acs.get_aliredis_instanceid(['region']):
        for redis_info in redis_instances:
            instance_id = redis_info.get('InstanceId')
            instance_name = redis_info.get('InstanceName')
            instance_infos[instance_id] = {'instance_name': instance_name}
    return instance_infos

def get_json(str):
    str_lst = str.split(',')
    lst = []
    for kv_str in str_lst:
        kv_lst = kv_str.split(':')
        lst.append('"{k}":"{v}"'.format(k=kv_lst[0], v=kv_lst[1]))
    res = '{' + ','.join(lst) + '}'
    return res

def main():
    if len(sys.argv) < 3:
        print('need metric and period args')
        metric = None
        period = None
        exit(1)
    else:
        metric = sys.argv[1]
        period = sys.argv[2]

    try:
        period = int(period)
    except Exception as err:
        print(err)
        print('wrong args type, period int')
        exit(2)

    if period % 60 != 0:
        print('wrong second arg, needs int, Multiple of 60')
        exit(4)

    instance_ids = '['
    instance_infos = get_instances()
    for instance_id in instance_infos.keys():
        instance_ids += '{{"instanceId": "{instance_id}" }},'.format(instance_id=instance_id)
    instance_ids += ']'
    acs = aliRedisMonitor('ali-key', 'ali-secret', 'region')
    monitor_infos = acs.get_ali_monitor_info(instance_ids, metric, period)
    infos_dic = {}
    for monitor_info in monitor_infos:
        current_value = monitor_info.get('Average')
        instance_id = monitor_info.get('instanceId')
        instance_name = instance_infos.get(instance_id).get('instance_name')
        infos_dic[instance_id] = {
                 "instance_name": instance_name,
                 "metric": metric,
                 "current_value": current_value,
        }
    infos_json = json.dumps(infos_dic)
    with open('/tmp/redis_{metric}_infos_json.txt'.format(metric=metric), 'w') as f:
        json.dump(infos_json, f)

if __name__ == '__main__':
    #main()
     try:
         main()
     except Exception as err:
         print('调用阿里云接口失败，非运维人员请忽略。')
         print(err)
         exit(1)
