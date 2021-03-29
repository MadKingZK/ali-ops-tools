#! /usr/bin/env /usr/bin/python3.7
import json
import sys
import settings

from aliyunsdkcore.client import AcsClient
from aliyunsdkcms.request.v20170301 import QueryMetricLastRequest


class AliMonitor(object):
    def __init__(self, ali_key, ali_secret):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )
        self.all_slb_info = self.load_slb_info()
        self.with_bandwidth_slb_info = self.load_slb_info(bondwidth=True)

    # 通过传入监控项名称返回该监控项下所有slb实例的当前信息。
    def get_monitor_info(self, metric, interval):
        request = QueryMetricLastRequest.QueryMetricLastRequest()
        request.set_accept_format('json')
        request.set_Project('acs_slb_dashboard')
        request.set_Metric(metric)
        request.set_Period(interval)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        infos = response_dict.get('Datapoints')
        return infos

    # 获取slb的基础信息, bondwidth=False返回所有slb信息；bondwidth=True，返回按带宽付费的slb信息
    def load_slb_info(self, bondwidth=False):
        if bondwidth:
            with open('/etc/zabbix/scripts/ali_slb_monitor/result_paybybandwidth_json.txt', 'r') as f:
                with_bandwidth_slb_info_json = json.load(f)
                with_bandwidth_slb_info = json.loads(with_bandwidth_slb_info_json)
                return with_bandwidth_slb_info
        else:
            with open('/etc/zabbix/scripts/ali_slb_monitor/result_all_json.txt', 'r') as f:
                all_slb_info_json = json.load(f)
                all_slb_info = json.loads(all_slb_info_json)
                return all_slb_info


def main():
    if len(sys.argv) < 3:
        metric = None
        interval = None
        print('need metric arg, if do not know it, look at the settings file')
        exit(1)
    else:
        metric = sys.argv[1]
        interval = sys.argv[2]
    if len(sys.argv) > 3:
        threshold_ratio = float(sys.argv[3])
    else:
        threshold_ratio = None
    if metric not in settings.threshold.get('default').keys():
        print('wrong arg, needs {keys} '.format(keys=settings.threshold.get('default').keys()))
        exit(2)
    elif not interval.isdigit():
        print('wrong second arg, needs int, Multiple of 60')
        exit(2)

    result = []
    alim = AliMonitor('ali-key', 'ali-secret')
    metrics_threshold = settings.threshold.get('default')
    # for metric, metric_threshold in metrics_threshold.items():
    metric_threshold = metrics_threshold.get(metric)
    metric_infos = alim.get_monitor_info(metric, interval)
    metric_description = settings.metric_description.get(metric)
    for metric_info in metric_infos:
        slb_id = metric_info.get('instanceId')
        port = metric_info.get('port')
        if not threshold_ratio:
            threshold_ratio = metric_threshold[0]
        value_method = metric_threshold[1]
        # computing_method = metric_threshold[2]
        value = metric_info.get(value_method)
        if metric == 'TrafficRXNew' or metric == 'TrafficTXNew':
            value = value / 1024 / 1024
            if alim.with_bandwidth_slb_info.get(slb_id):
                slb_name = alim.with_bandwidth_slb_info.get(slb_id).get(port).get('loadbalancername')
                bandwidth = alim.with_bandwidth_slb_info.get(slb_id).get(port).get('bandwidth')
                threshold_value = bandwidth * threshold_ratio
                if value > threshold_value:
                    alert_info = '{metric_description}: {slb_name}: {value:.2f} > {threshold_value:.2f}（带宽:{bandwidth}）'.format(
                        metric_description=metric_description,
                        slb_name=slb_name,
                        value=value,
                        threshold_value=threshold_value,
                        bandwidth=bandwidth)
                    result.append(alert_info)
        else:
            if alim.all_slb_info.get(slb_id):
                slb_name = alim.all_slb_info.get(slb_id).get('loadbalancername')
                threshold_value = threshold_ratio

                if value > threshold_value:
                    alert_info = '{metric_description}: {slb_name}: {value} > {threshold_value}'.format(
                        metric_description=metric_description,
                        slb_name=slb_name,
                        value=value,
                        threshold_value=threshold_value)
                    result.append(alert_info)

    print('\n'.join(result))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('调用阿里云接口失败，非运维人员请忽略。')
        print(err)
