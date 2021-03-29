#!/usr/bin/env python3
from pyzabbix import ZabbixAPI

class ZabbixMonitor(object):
    def __init__(self, user, password, url):
        self.prioritytostr = {'0': 'ok', '1': '信息', '2': '警告', '3': '严重'}  # 告警级别
        self.user = user
        self.password = password
        self.url = url
        self.zapi = ZabbixAPI(self.url)
        self.zapi.login(self.user, self.password)

    def getHosts(self):
        hosts = self.zapi.host.get(
            output="hostid",
            monitored_hosts=None,
        )
        return hosts

zbxmon = ZabbixMonitor('madking', 'madking123', 'http://zabbix.madblog.cn')
hosts = zbxmon.getHosts()
hostids = [ host.get('hostid') for host in hosts ]
print(' '.join(hostids))
