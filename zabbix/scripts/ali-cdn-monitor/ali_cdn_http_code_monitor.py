#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, os
import urllib, urllib2
import base64
import hmac
import hashlib
from hashlib import sha1
import time
import uuid
import json
from optparse import OptionParser
import ConfigParser
import traceback
import datetime

access_key_id = 'ali-key';
access_key_secret = 'ali-secret';
cdn_server_address = 'https://cdn.aliyuncs.com'
CONFIGFILE = os.getcwd() + '/aliyun.ini'
CONFIGSECTION = 'Credentials'
cmdlist = '''
接口说明请参照pdf文档
'''

extra_param = {}

def percent_encode(str):
    #res = urllib.quote(str.decode(sys.stdin.encoding).encode('utf8'), '')
    res = urllib.quote(str.decode("utf-8").encode('utf8'), '')

    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')

    return res


def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
    os.getcwd() + '/aliyun.ini.bak'
    canonicalizedQueryString = ''
    for (k, v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)

    stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])

    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature


def compose_url(user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # timestamp = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", t)
    http_xxx = user_params.pop("HttpCode", None)
    extra_param["HttpCode"] = http_xxx

    parameters = { \
        'Format': 'JSON', \
        'Version': '2018-05-10', \
        'AccessKeyId': access_key_id, \
        'SignatureVersion': '1.0', \
        'SignatureMethod': 'HMAC-SHA1', \
        'SignatureNonce': str(uuid.uuid1()), \
        'Timestamp': timestamp, \
        'Interval': "300",
        'EndTime': get_time()
        }
    # print user_params.items()
    for key in user_params.keys():
        if key == "StartTime":
            parameters[key] = get_time(int(user_params[key]))
        else:
            parameters[key] = user_params[key]

    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    # print http_xxx
    # print parameters
    url = cdn_server_address + "/?" + urllib.urlencode(parameters)
    return url


def get_response(user_params, quiet=False, method='read'):
    url = compose_url(user_params)
    result = urllib.urlopen(url)
    return getattr(result, method, 'read')()

def handle_code_data(data):
    result = {"4xx": [], "5xx": []}
    data = json.loads(data) if isinstance(data, str) else data

    value = data.get("HttpCodeData").get("UsageData")
    for val in value:
        for code in val.get("Value").get("CodeProportionData"):
            if code.get("Code").startswith("4"):
                result["4xx"].append(float(code.get("Proportion")))
            elif code.get("Code").startswith("5"):
                result["5xx"].append(float(code.get("Proportion")))

    return result

def http_4xx(data):
    r = 0
    #print max(data.get("4xx"))
    #return None
    try:
        r = max(data.get("4xx"))
    except Exception as e:
        print r
    else:
        print r

def http_default(data):
    print 0

def http_5xx(data):
    # print data
    r = 0
    #print max(data.get("5xx"))
    #return None
    try:
        r = max(data.get("5xx"))
    except Exception as e:
        print r
    else:
        print r

def handle_data(data):
    print data
    data = json.loads(data) if isinstance(data, str) else data
    max_all_value = 0
    count = 0
    max_https_value = 0
    for value in data.values():
        if isinstance(value, dict):
            for x in value["DataModule"]:
                count += 1
                cur_all = x.get("Value", 0)
                if cur_all > max_all_value:
                    max_all_value = cur_all
    print max_all_value


def configure_accesskeypair(args, options):
    if options.accesskeyid is None or options.accesskeysecret is None:
        print("config miss parameters, use --id=[accesskeyid] --secret=[accesskeysecret]")
        sys.exit(1)
    config = ConfigParser.RawConfigParser()
    config.add_section(CONFIGSECTION)
    config.set(CONFIGSECTION, 'accesskeyid', options.accesskeyid)
    config.set(CONFIGSECTION, 'accesskeysecret', options.accesskeysecret)
    cfgfile = open(CONFIGFILE, 'w+')
    config.write(cfgfile)
    cfgfile.close()


def setup_credentials():
    config = ConfigParser.ConfigParser()
    try:
        config.read(CONFIGFILE)
        global access_key_id
        global access_key_secret
        access_key_id = config.get(CONFIGSECTION, 'accesskeyid')
        access_key_secret = config.get(CONFIGSECTION, 'accesskeysecret')
    except Exception, e:
        print traceback.format_exc()
        print("can't get access key pair, use config --id=[accesskeyid] --secret=[accesskeysecret] to setup")
        sys.exit(1)


def get_time(*args):
    now = time.time()
    if args:
        uts = datetime.datetime.utcfromtimestamp(now-args[0])
    else:
        uts = datetime.datetime.utcfromtimestamp(now)
    return uts.strftime("%Y-%m-%dT%H:%M:%SZ")


def timefmt(t, fmt="%Y%m%d%H%M%S"):
    # %Y-%m-%dT%H:%M:%SZ
    s = time.strptime(t, fmt)
    timestamp = time.mktime(s)
    uts = datetime.datetime.utcfromtimestamp(timestamp)
    return uts.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == '__main__':
    parser = OptionParser("%s Action=action Param1=Value1 Param2=Value2\n" % sys.argv[0])
    parser.add_option("-i", "--id", dest="accesskeyid", help="specify access key id")
    parser.add_option("-s", "--secret", dest="accesskeysecret", help="specify access key secret")

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    if args[0] == 'help':
        print cmdlist
        sys.exit(0)
    if args[0] != 'config':
        # setup_credentials()
        pass
    else:  # it's a configure id/secret command
        configure_accesskeypair(args, options)
        sys.exit(0)

    user_params = {}
    idx = 1
    if not sys.argv[1].lower().startswith('action='):
        user_params['action'] = sys.argv[1]
        idx = 2

    for arg in sys.argv[idx:]:
        try:
            key, value = arg.split('=')
            user_params[key.strip()] = value
        except ValueError, e:
            print(e.read().strip())
            raise SystemExit(e)

    ret = get_response(user_params)
    data = handle_code_data(ret)
    #globals().get(extra_param.get("HttpCode", "http_default"))(data)
    if extra_param.get("HttpCode") == "http_4xx":
        http_4xx(data)
    elif extra_param.get("HttpCode") == "http_5xx":
        http_5xx(data)
    else:
        http_default(data)

