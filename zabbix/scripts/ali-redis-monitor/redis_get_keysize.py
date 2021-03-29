#!/usr/bin/env python3.7

import sys

from redis import StrictRedis
from redis_pwd_cfg import redis_pwd_dic

def get_size(r, key_name, key_type):
    if key_type == b'zset':
        return r.zcard(key_name)
    if key_type == b'set':
        return r.scard(key_name)
    if key_type == b'list':
        return r.llen(key_name)
    return None

if __name__ == '__main__':

    try:
        redis_host = sys.argv[1]
        redis_port = sys.argv[2]
        redis_db = sys.argv[3]
        redis_key = sys.argv[4]
        redis_instanse = redis_host.split('.')[0]
        redis_password = redis_pwd_dic.get(redis_instanse)
        if not redis_password:
            print(-1)
            sys.exit(1)
        r = StrictRedis(host=redis_host, port=redis_port, password=redis_password, db=redis_db, decode_responses=False)

        print(get_size(r, redis_key, r.type(redis_key)))
    except Exception as e:
        print(-1)
