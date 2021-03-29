#! /usr/bin/env /usr/bin/python3.7
from aliyunsdkcore.client import AcsClient
from aliyunsdkdds.request.v20151201 import DescribeDBInstancesRequest
from aliyunsdkcms.request.v20170301 import QueryMetricLastRequest
import json, sys


class aliMongodbMonitor():
    def __init__(self, ali_key, ali_secret, region_id):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )
        # 创建AcsClient实例
        self.client.set_region_id(region_id)

    def getAliMongoInstanceid(self):
        # 设置初始页码
        pageNumber = 1

        request = DescribeDBInstancesRequest.DescribeDBInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(30)
        request.set_PageNumber(pageNumber)

        # 发起API请求并显示返回值
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)

        # 生成生成器
        while response_dict.get('DBInstances').get('DBInstance'):
            yield response_dict.get('DBInstances').get('DBInstance')
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

    def get_ali_monitor_info(self, instances_ids, metric, period):
        # 实例化request
        request = QueryMetricLastRequest.QueryMetricLastRequest()
        # 组装request，接手json，监控流出流量，周期300s
        request.set_accept_format('json')
        request.set_Project('acs_mongodb')
        request.set_Metric(metric)
        request.set_Period(period)
        request.set_Dimensions(instances_ids)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        infos = response_dict.get('Datapoints')
        return infos


def get_group_instances(group_name):
    instance_infos = {}
    acs = aliMongodbMonitor('ali-key', 'ali-secret', 'region')
    for redis_instances in acs.getAliMongoInstanceid():
        for redis_info in redis_instances:
            instance_id = redis_info.get('DBInstanceId')
            instance_name = redis_info.get('DBInstanceDescription')
            group = instance_name.split('-', maxsplit=1)[0]
            if group == group_name:
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
    special_threshold = None
    if len(sys.argv) < 5:
        print('need instanceid, metric and period args')
        group = None
        metric = None
        period = None
        default_threshold = None
        exit(1)
    else:
        group = sys.argv[1]
        metric = sys.argv[2]
        period = sys.argv[3]
        default_threshold = sys.argv[4]
        if len(sys.argv) >= 6:
            special_threshold = sys.argv[5]

    try:
        default_threshold = int(default_threshold)
        period = int(period)
    except Exception as err:
        print(err)
        print('wrong args type, threshold int, period int')
        exit(2)

    if special_threshold:
        try:
            special_threshold = get_json(special_threshold)
            special_threshold = json.loads(special_threshold)
        except Exception as err:
            print(err)
            print('special_threshold needs json type')
            exit(2)

    if period % 60 != 0:
        print('wrong second arg, needs int, Multiple of 60')
        exit(4)
    instance_ids = '['
    instance_infos = get_group_instances('xbd')
    for instance_id in instance_infos.keys():
        instance_ids += '{{"instanceId": "{instance_id}" }},'.format(instance_id=instance_id)
    instance_ids += ']'
    acs = aliMongodbMonitor('ali-key', 'ali-secret', 'region')
    monitor_infos = acs.get_ali_monitor_info(instance_ids, metric, period)
    alert_infos = []
    for monitor_info in monitor_infos:
        current_value = monitor_info.get('Average')
        alert_instance_id = monitor_info.get('instanceId')
        role = monitor_info.get('role')
        if special_threshold and alert_instance_id in special_threshold.keys():
            real_threshold = int(special_threshold.get(alert_instance_id))
        else:
            real_threshold = default_threshold
        if current_value > real_threshold:
            instance_name = instance_infos.get(alert_instance_id).get('instance_name')
            alert_infos.append(
                '【{instance_name}：{role}】{metric}: {current_value} > {real_threshold}'.format(
                    instance_name=instance_name, role=role, metric=metric, current_value=current_value,
                    real_threshold=real_threshold))
    alert_info_str = '\n'.join(alert_infos)
    print(alert_info_str)

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('调用阿里云接口失败，非运维人员请忽略。')
        print(err)
        exit(1)
