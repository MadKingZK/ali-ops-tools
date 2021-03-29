#! /usr/bin/env /usr/bin/python3.7
# -*- coding: utf8 -*-
from aliyunsdkcore.client import AcsClient
from aliyunsdkcdn.request.v20141111 import DescribeUserDomainsRequest
import json


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

    def get_cdn_info(self):
        pageNumber = 1
        request = DescribeUserDomainsRequest.DescribeUserDomainsRequest()
        request.set_PageNumber(pageNumber)
        request.set_PageSize(50)
        request.set_accept_format('json')
        response = self.client.do_action_with_exception(request)
        response_dict = json.loads(response)

        # 生成生成器
        while response_dict.get('Domains').get('PageData'):
            yield response_dict.get('Domains').get('PageData')
            pageNumber += 1
            request.set_PageNumber(pageNumber)
            response = self.client.do_action_with_exception(request)
            response_dict = json.loads(response)


def main():

    result_cdn_all = list()
    acs = AliSlbTools('ali-key', 'ali-secret', 'region')
    get_cdn_infos = acs.get_cdn_info()
    for cdn_infos in get_cdn_infos:
        for cdn_info in cdn_infos:
            result_cdn_all.append(cdn_info.get("DomainName"))

    print(json.dumps(result_cdn_all))

    result_all_json = json.dumps(result_cdn_all, ensure_ascii=False)
    with open('/etc/zabbix/scripts/ali_cdn_monitor/result_cdn_all_json.txt', 'w') as fall:
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
