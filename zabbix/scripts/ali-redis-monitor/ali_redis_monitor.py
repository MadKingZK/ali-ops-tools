#! /usr/bin/env /usr/bin/python3.7
from aliyunsdkcore.client import AcsClient
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

def main():
    if len(sys.argv) < 4:
        print('need instanceid, metric and period args')
        instance_id = None
        metric = None
        period = None
        exit(1)
    else:
        instance_id = sys.argv[1]
        metric = sys.argv[2]
        period = sys.argv[3]

    instance_ids = '[{{"instanceId":"{instance_id}"}}]'.format(instance_id=instance_id)
    acs = aliRedisMonitor('ali-key', 'ali-secret', 'region')
    res = acs.get_ali_monitor_info(instance_ids, metric, period)
    print(res[0].get('Average'))

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('调用阿里云接口失败，非运维人员请忽略。')
        print(err)
