#! /usr/bin/env /usr/bin/python3.7
import sys
import json

if len(sys.argv) >= 3:
    instance_id = sys.argv[1]
    metric = sys.argv[2]
else:
    instance_id = None
    metric = None
    print(len(sys.argv))
    print('needs instance_id and mertric args')
    exit(1)

with open('/tmp/redis_{metric}_infos_json.txt'.format(metric=metric), 'r') as f:
    #print('/tmp/redis_{metric}_infos_json.txt'.format(metric=metric))
    redis_infos_json = json.load(f)
    redis_infos_dic = json.loads(redis_infos_json)

redis_info = redis_infos_dic.get(instance_id)
current_value = redis_info.get("current_value")
real_metric = redis_info.get('metric')
if metric == real_metric:
    print(current_value)
else:
    print('error metric')
