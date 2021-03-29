#! /usr/bin/env /usr/bin/python3.7
import datetime
import pymysql.cursors

# 连接配置信息
config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'monitor',
    'password': 'monitor',
    'db': 'zabbix',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}
#flags
discovery = 1
#stat
not_supported = 1
#status
disabled_item = 1

# 创建连接
connection = pymysql.connect(**config)

# 执行sql语句
'''
[{'name': 'authorized_keys_path', 'key_': 'discovery.authorized_keys_path', 'hostid': 10328, 'error': 'Value should be a JSON object.', 'status': 0, 'state': 0}]
ova-ops-ansible-01(10.27.184.51)
'''

try:
    with connection.cursor() as cursor:
        # 执行sql语句，进行查询
        get_diserr_sql = 'SELECT name, hostid, error, status, state  FROM items  WHERE flags={discovery} AND (state={not_supported} OR status={disabled_item} OR error!="")'.format(discovery=discovery, not_supported=not_supported, disabled_item=disabled_item)
        #sql = 'SELECT * FROM items LIMIT 10;'

        cursor.execute(get_diserr_sql)
        # 获取查询结果
        results = cursor.fetchall()
        for res in results:
            hostid = res.get('hostid')
            if hostid:
              get_hostalias_sql = 'SELECT name FROM hosts WHERE hostid={hostid}'.format(hostid=hostid)
              cursor.execute(get_hostalias_sql)
              result = cursor.fetchone()
              host_alias = result.get('name')
            else:
                host_alias = 'NotGet'
            print('主机名:{hostalias}, 自动发现名:{dis_name}, 状态:{status},状况:{state} 信息:{info}'.format(hostalias=host_alias,
                                                                                                  dis_name=res.get('name'),
                                                                                                  status= '已启用' if res.get('staus')==0 else '已禁用',
                                                                                                  state='正常' if res.get('state')==0 else '不正常',
                                                                                                  info=res.get('error')[0:20]))

finally:
    connection.close()
