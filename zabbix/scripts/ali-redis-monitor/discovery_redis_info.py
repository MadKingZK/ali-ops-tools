#! /usr/bin/env /usr/bin/python3.7
# -*- coding: utf8 -*-
from aliyunsdkcore.client import AcsClient
from aliyunsdkr_kvstore.request.v20150101 import DescribeInstancesRequest
import redis, json, sys
from redis_pwd_cfg import redis_pwd_dic


class aliApiTools():
    def __init__(self, ali_key, ali_secret):
        self.ali_key = ali_key
        self.ali_secret = ali_secret
        self.client = AcsClient(
            self.ali_key,
            self.ali_secret,
        )

    def getAliRedisInstanceid(self, regionids):
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


class discoveryRedis():
    def __init__(self, host, port, password=''):
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        self.redis_info_dic = self.get_info()

    def test_conn(self):
        res = self.redis_client.execute_command('ping')
        if (res == 'PONG'):
            return True
        else:
            return False

    def get_info(self):
        res = self.redis_client.execute_command('info all')
        res = res.split('\r\n')
        res_dic = {}
        for s in res:
            if s.strip() and not s.startswith('#'):
                kv_list = s.split(':')
                res_dic[kv_list[0]] = kv_list[1]
        return res_dic

    def discovery_commands(self):
        commands_lst = []
        for key in self.redis_info_dic.keys():
            if key.startswith('cmdstat'):
                commands_lst.append(key)
        return commands_lst

    def dump_redis_stats_report(self):
        redis_info_file = '/tmp/redis-{host}-{port}'.format(host=self.host, port=self.port)
        redis_slow_len_file = '/tmp/redis-{host}-{port}-slowlog-len'.format(host=self.host, port=self.port)
        redis_slow_raw_file = '/tmp/redis-{host}-{port}-slowlog-raw'.format(host=self.host, port=self.port)
        redis_max_clients_file = '/tmp/redis-{host}-{port}-maxclients'.format(host=self.host, port=self.port)

        redis_info = self.redis_client.execute_command('info all')
        redis_slow_len = self.redis_client.execute_command('slowlog len')
        # redis_slow_raws = self.redis_client.execute_command('slowlog get')
        # for slow_log in redis_slow_raws:
        #     slow_cmd = ''
        #     for cmdword in slow_log[-1]:
        #         slow_cmd += cmdword + ' '
        #     output_dic = {"slowLogId": slow_log[0],
        #                   "slowLogTS": slow_log[1],
        #                   "duration": slow_log[2],
        #                   "slowCmd": slow_cmd.strip()}
        #     print(output_dic)
        redis_max_clients = self.redis_client.execute_command('config get *"maxclients"*')
        with open(redis_info_file, 'w') as f1:
            f1.write(str(redis_info))
        with open(redis_slow_len_file, 'w') as f2:
            f2.write(str(redis_slow_len))
        # with open(redis_slow_raw_file, 'w') as f3:
        #    f3.write(str(redis_slow_raw))
        with open(redis_max_clients_file, 'w') as f4:
            f4.write(str(redis_max_clients))


if __name__ == '__main__':

    arg = None
    if len(sys.argv) <= 1:
        print('need general or command arg')
    else:
        arg = sys.argv[1]

    key = 'ali-key'
    secret = 'ali-secret'

    apitools = aliApiTools(key, secret)
    result = {
        "data": []
    }

    if arg == 'general':
        for redis_instances_infos in apitools.getAliRedisInstanceid(['region']):
            for redis_info in redis_instances_infos:
                try:
                    redis_pwd = redis_pwd_dic[redis_info.get('InstanceId')]
                    ali_redis = discoveryRedis(redis_info.get("ConnectionDomain"), redis_info.get("Port"), redis_pwd)
                    check = "true" if ali_redis.test_conn() else "false"
                    #check = ali_redis.test_conn()
                    group = redis_info.get('InstanceName').split('-', maxsplit=1)[0]
                except Exception as err:
                    group = redis_info.get('InstanceName').split('-', maxsplit=1)[0]
                    info_dic = {
                        "{#INSTANCEID}": redis_info.get('InstanceId'),
                        "{#INSTANCENAME}": redis_info.get('InstanceName'),
                        "{#CONNECTIONDOMAIN}": redis_info.get("ConnectionDomain"),
                        "{#PORT}": redis_info.get("Port"),
                        "{#CHECK}": "false",
                        "{#GROUP}": group,
                    }
                    result['data'].append(info_dic)
                    continue
                ali_redis.dump_redis_stats_report()
                info_dic = {
                    "{#INSTANCEID}": redis_info.get('InstanceId'),
                    "{#INSTANCENAME}": redis_info.get('InstanceName'),
                    "{#CONNECTIONDOMAIN}": redis_info.get("ConnectionDomain"),
                    "{#PORT}": redis_info.get("Port"),
                    "{#CHECK}": check,
                    "{#GROUP}": group,
                }
                result['data'].append(info_dic)
        result_json = json.dumps(result)
        print(result_json)

    elif arg == 'cluster':
        for redis_instances_infos in apitools.getAliRedisInstanceid(['region']):
            for redis_info in redis_instances_infos:
                if redis_info.get("ArchitectureType") == "cluster":
                    try:
                        redis_pwd = redis_pwd_dic[redis_info.get('InstanceId')]
                        ali_redis = discoveryRedis(redis_info.get("ConnectionDomain"), redis_info.get("Port"), redis_pwd)
                        check = "true" if ali_redis.test_conn() else "false"
                        #check = ali_redis.test_conn()
                        group = redis_info.get('InstanceName').split('-', maxsplit=1)[0]
                    except Exception as err:
                        continue
                    #ali_redis.dump_redis_stats_report()

                    host = redis_info.get("ConnectionDomain")
                    password = redis_pwd_dic[redis_info.get('InstanceId')]
                    r = redis.StrictRedis(host=host, port=6379, password=password)
                    nodecount = r.info()['nodecount']
                    for node in range(0, nodecount):
                        info_dic = {
                            "{#INSTANCEID}": redis_info.get('InstanceId'),
                            "{#INSTANCENAME}": redis_info.get('InstanceName'),
                            "{#INSTANCENODE}": str(node),
                            "{#CONNECTIONDOMAIN}": redis_info.get("ConnectionDomain"),
                            "{#GROUP}": group,
                        }
                        result['data'].append(info_dic)
        result_json = json.dumps(result)
        print(result_json)

    elif arg == 'commands':
        for redis_instances_infos in apitools.getAliRedisInstanceid(['region']):
            for redis_info in redis_instances_infos:
                try:
                    redis_pwd = redis_pwd_dic[redis_info.get('InstanceId')]
                    ali_redis = discoveryRedis(redis_info.get("ConnectionDomain"), redis_info.get("Port"), redis_pwd)
                    check = "true" if ali_redis.test_conn() else "false"
                    #check = ali_redis.test_conn()
                    group = redis_info.get('InstanceName').split('-', maxsplit=1)[0]
                except Exception as err:
                    group = redis_info.get('InstanceName').split('-', maxsplit=1)[0]
                    info_dic = {
                        "{#INSTANCEID}": redis_info.get('InstanceId'),
                        "{#INSTANCENAME}": redis_info.get('InstanceName'),
                        "{#CONNECTIONDOMAIN}": redis_info.get("ConnectionDomain"),
                        "{#PORT}": redis_info.get("Port"),
                        "{#CHECK}": "false",
                        "{#GROUP}": group,
                    }
                    result['data'].append(info_dic)
                    continue
                ali_redis.test_conn()
                commands_lst = ali_redis.discovery_commands()
                for command in commands_lst:
                    info_dic = {
                        "{#INSTANCEID}": redis_info.get('InstanceId'),
                        "{#INSTANCENAME}": redis_info.get('InstanceName'),
                        "{#CONNECTIONDOMAIN}": redis_info.get("ConnectionDomain"),
                        "{#PORT}": redis_info.get("Port"),
                        "{#COMMAND}": command,
                        "{#CHECK}": check,
                        "{#GROUP}": group,
                    }
                    result['data'].append(info_dic)
        result_json = json.dumps(result)
        print(result_json)
