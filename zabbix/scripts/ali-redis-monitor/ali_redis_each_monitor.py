#! /usr/bin/env /usr/bin/python3.7
import json
import sys
import settings

def main():
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
        redis_infos_json = json.load(f)
        redis_infos_dic = json.loads(redis_infos_json)

    redis_info = redis_infos_dic.get(instance_id)
    current_value = redis_info.get("current_value")
    real_metric = redis_info.get('metric')
    if metric != real_metric:
        print('error metric')
        exit(1)

    thresholds_dic = settings.threshold.get(metric)
    if thresholds_dic:
        threshold = thresholds_dic.get(instance_id)
        if not threshold:
            threshold = thresholds_dic.get('default')
    else:
        threshold = 80

    if current_value > threshold:
        instance_name = redis_info.get('instance_name')
        print('【{instance_name}】{metric}: {current_value} > {threshold}'.format(instance_name=instance_name, metric=metric,
                                                                   current_value=current_value,threshold=threshold))

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('脚本执行出错，非运维人员请忽略。')
        print(err)
        exit(1)
