#!/usr/bin/env python
# -*- coding: utf-8 -*-  
import json
import sys
import redis
from redis_pwd_cfg import redis_pwd_dic
from redis._compat import nativestr
from aliyunsdkcore import client
from aliyunsdkcore.request import CommonRequest

"""
Redis集群实例规格表
规格    InstanceClass （API 使用）  最大连接数  最大吞吐量 （MB）
16 GB 集群版    redis.sharding.small.default    80000   384
32 GB 集群版    redis.sharding.mid.default  80000   384
64 GB 集群版    redis.sharding.large.default    80000   384
128 GB 集群版   redis.sharding.2xlarge.default  160000  768
256 GB 集群版   redis.sharding.4xlarge.default  160000  768
16 GB 集群单机版    redis.sharding.basic.small.default  80000   384
32 GB 集群单机版    redis.sharding.basic.mid.default    80000   384
64 GB 集群单机版    redis.sharding.basic.large.default  80000   384
128 GB 集群单机版   redis.sharding.basic.2xlarge.default    160000  768
256 GB 集群单机版   redis.sharding.basic.4xlarge.default    160000  768
"""

SPEC = {
    "redis.sharding.small.default": {"maxmemory": 17179869184, "maxconn": 80000, "maxio": 384},
    "redis.sharding.mid.default": {"maxmemory": 34359738368, "maxconn": 80000, "maxio": 384},
    "redis.sharding.large.default": {"maxmemory": 68719476736, "maxconn": 80000, "maxio": 384},
    "redis.sharding.2xlarge.default": {"maxmemory": 137438953472, "maxconn": 160000, "maxio": 768},
    "redis.sharding.4xlarge.default": {"maxmemory": 274877906944, "maxconn": 160000, "maxio": 768},
    "redis.sharding.basic.small.default": {"maxmemory": 17179869184, "maxconn": 80000, "maxio": 384},
    "redis.sharding.basic.mid.default": {"maxmemory": 34359738368, "maxconn": 80000, "maxio": 384},
    "redis.sharding.basic.large.default": {"maxmemory": 68719476736, "maxconn": 80000, "maxio": 384},
    "redis.sharding.basic.2xlarge.default": {"maxmemory": 137438953472, "maxconn": 160000, "maxio": 768},
    "redis.sharding.basic.4xlarge.default": {"maxmemory": 274877906944, "maxconn": 160000, "maxio": 768}
    }

def parse_info(response):
  "Parse the result of Redis's INFO command into a Python dict"
  info = {}
  response = nativestr(response)
  def get_value(value):
    if ',' not in value or '=' not in value:
      try:
        if '.' in value:
          return float(value)
        else:
          return int(value)
      except ValueError:
        return value
    else:
      sub_dict = {}
      for item in value.split(','):
        k, v = item.rsplit('=', 1)
        sub_dict[k] = get_value(v)
      return sub_dict
  for line in response.splitlines():
    if line and not line.startswith('#'):
      if line.find(':') != -1:
        key, value = line.split(':', 1)
        info[key] = get_value(value)
      else:
        # if the line isn't splittable, append it to the "__raw__" key
        info.setdefault('__raw__', []).append(line)
  return info
if __name__ == '__main__':
  if len(sys.argv) != 4:
    print 'Usage: python ', sys.argv[0], ' instansid host threshold'
    exit(1)
  instance_id = sys.argv[1]
  host = sys.argv[2]
  node = sys.argv[3]
  password = redis_pwd_dic.get(instance_id)
  r = redis.StrictRedis(host=host, port=6379, password=password)
  info = r.execute_command("iinfo", str(node))
  #print(info)
  info_res = parse_info(info)
  maxmemory = info_res.get('maxmemory')
  if not maxmemory:
    client = client.AcsClient('ali-key','ali-secret','region')
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('r-kvstore.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('https') # https | http
    request.set_version('2015-01-01')
    request.set_action_name('DescribeInstanceAttribute')

    request.add_query_param('RegionId', 'region')
    request.add_query_param('InstanceId', instance_id)

    response = client.do_action(request)
    json_result = json.loads(response)
    instance_class = json_result.get('Instances').get('DBInstanceAttribute')[0].get('InstanceClass')
    maxmemory = SPEC.get(instance_class).get('maxmemory') / 8
    #info_res = parse_info(info)
    #print(info_res)

  usedmem = info_res.get('used_memory')
  #print(type(maxmemory),type(usedmem))
  percent = int(round(float(usedmem)/float(maxmemory)*100,0))
  print(percent)
