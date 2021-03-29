#! /usr/bin/env /usr/bin/python3.7
# -*- coding: utf8 -*-
import json
from copy import deepcopy
from aliyunsdkcore.client import AcsClient
from aliyunsdkslb.request.v20140515 import DescribeLoadBalancersRequest, DescribeLoadBalancerTCPListenerAttributeRequest, DescribeLoadBalancerHTTPListenerAttributeRequest, DescribeLoadBalancerHTTPSListenerAttributeRequest, DescribeLoadBalancerAttributeRequest

class AliSlbTools(object):
    def __init__(self, ali_key, ali_secret, region_id):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )
        self.region_id = region_id
        self.client.set_region_id(self.region_id)

    def get_internet_type_slb(self, withbandwidth=False):
        pageNumber = 1
        request = DescribeLoadBalancersRequest.DescribeLoadBalancersRequest()
        request.set_PageSize(10)
        request.set_PageNumber(pageNumber)
        request.set_accept_format('json')
        request.set_AddressType('internet')
        request.set_NetworkType('classic')
        request.set_LoadBalancerStatus('active')
        if withbandwidth:
            request.set_InternetChargeType('paybybandwidth')
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        # 生成生成器
        while response_dict.get('LoadBalancers').get('LoadBalancer'):
            yield response_dict.get('LoadBalancers').get('LoadBalancer')
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)

    def get_slb_attr(self, slb_id):
        request = DescribeLoadBalancerAttributeRequest.DescribeLoadBalancerAttributeRequest()
        request.set_accept_format('json')
        request.set_LoadBalancerId(slb_id)
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)
        return response_dict

    def get_slb_listener_ports(self, slb_id):
        res = self.get_slb_attr(slb_id)
        ports_and_protos = res.get('ListenerPortsAndProtocol').get('ListenerPortAndProtocol')
        port_infos = []
        for port_and_proto in ports_and_protos:
            proto = port_and_proto.get('ListenerProtocol')
            port = port_and_proto.get('ListenerPort')
            info_dic = {
                'proto': proto,
                'port': port,
            }
            port_infos.append(info_dic)
        return port_infos

    def get_slb_tcp_attr(self, slb_id, port):
        request = DescribeLoadBalancerTCPListenerAttributeRequest.DescribeLoadBalancerTCPListenerAttributeRequest()
        request.set_accept_format('json')
        request.set_LoadBalancerId(slb_id)
        request.set_ListenerPort(port)
        try:
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)
        except Exception as err:
            return False
        return response_dict

    def get_slb_http_attr(self, slb_id, port):
        request = DescribeLoadBalancerHTTPListenerAttributeRequest.DescribeLoadBalancerHTTPListenerAttributeRequest()
        request.set_accept_format('json')
        request.set_LoadBalancerId(slb_id)
        request.set_ListenerPort(port)
        try:
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)
        except Exception as err:
            return False
        return response_dict

    def get_slb_https_attr(self,slb_id, port):
        request = DescribeLoadBalancerHTTPSListenerAttributeRequest.DescribeLoadBalancerHTTPSListenerAttributeRequest()
        request.set_accept_format('json')
        request.set_LoadBalancerId(slb_id)
        request.set_ListenerPort(port)
        try:
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)
            return response_dict
        except Exception as err:
            return False

    def get_slb_port_attr(self, slb_id, port, proto):
        if proto == 'tcp':
            return self.get_slb_tcp_attr(slb_id, port)
        elif proto == 'http':
            return self.get_slb_http_attr(slb_id, port)
        elif proto == 'https':
            return self.get_slb_https_attr(slb_id, port)
        else:
            return False

def main():
    result_all = {}
    result_paybybandwidth = {}
    acs = AliSlbTools('ali-key', 'ali-secret', 'region')
    get_withbandwidth_infos = acs.get_internet_type_slb(withbandwidth=True)
    for slb_infos in get_withbandwidth_infos:
        for slb_info in slb_infos:
            slb_id = slb_info.get('LoadBalancerId')
            info_dic = {
                "loadbalancername": slb_info.get('LoadBalancerName'),
                "regionid": slb_info.get('RegionId'),
                "address": slb_info.get('Address'),
            }

            port_infos = acs.get_slb_listener_ports(slb_info.get('LoadBalancerId'))
            for port_info in port_infos:
                port = port_info.get('port')
                proto = port_info.get('proto')
                res = acs.get_slb_port_attr(slb_id, port, proto)
                if res.get('Status') == 'running' and res.get('Bandwidth') > 0:
                    info_dic['proto'] = proto
                    info_dic['bandwidth'] = res.get('Bandwidth')
                    if slb_id in result_paybybandwidth.keys():
                        result_paybybandwidth[slb_id][port] = deepcopy(info_dic)
                    else:
                        result_paybybandwidth[slb_id] = {}
                        result_paybybandwidth[slb_id][port] = deepcopy(info_dic)
    result_paybybandwidth_json = json.dumps(result_paybybandwidth, ensure_ascii=False)
    with open('/etc/zabbix/scripts/ali_slb_monitor/result_paybybandwidth_json.txt', 'w') as fpbd:
        json.dump(result_paybybandwidth_json, fpbd)

    get_all_infos = acs.get_internet_type_slb()
    for slb_infos in get_all_infos:
        for slb_info in slb_infos:
            slb_id = slb_info.get('LoadBalancerId')
            info_dic = {
                "loadbalancername": slb_info.get('LoadBalancerName'),
                "regionid": slb_info.get('RegionId'),
                "address": slb_info.get('Address'),
            }
            result_all[slb_id] = deepcopy(info_dic)
    result_all_json = json.dumps(result_all, ensure_ascii=False)
    with open('/etc/zabbix/scripts/ali_slb_monitor/result_all_json.txt', 'w') as fall:
        json.dump(result_all_json, fall)

outdict = {
    "data":[
        {"{#DISCOVERYREDIS}": True},
    ]
}
outjson = json.dumps(outdict)
print(outjson)

if __name__ == '__main__':
    main()
