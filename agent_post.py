import requests
import time
def god1():
    app_key = '66244932-3a61-48c5-b847-9a750ba6567e'

    data_dict = {
        'k1':'v1',
        'v2':'v2'
    }
    ret = requests.post(
        url='http://127.0.0.1:8000/api/asset1.html',
        params={'app_key': app_key},
        data=data_dict
    )
    print(ret.text)

def god2():
    def create_md5(app_key,app_secret,timestamp):
        import hashlib

        m = hashlib.md5(bytes(app_secret,encoding='utf-8'))
        temp = "%s|%s" %(app_key,timestamp,)
        m.update(bytes(temp,encoding='utf-8'))
        return m.hexdigest()

    app_key = '66244932-3a61-48c5-b847-9a750ba6567e'
    app_secret = "asd=asdfkdf"
    app_timestamp = time.time()
    app_sign = create_md5(app_key,app_secret,app_timestamp)


    data_dict = {
        'k1':'v1',
        'v2':'v2'
    }
    ret = requests.post(
        url='http://127.0.0.1:8000/api/asset2.html',
        params={'app_sign': app_sign,"app_key": app_key, 'app_timestamp': app_timestamp},
        data=data_dict
    )

    print(ret.text)


def god3():
    data_dict = {
        'message': None,
        'error': None,
        'status': True,
        'data': {
            'hostname': 'retail-gms-001',
            'os_platform': 'linux',
            'cpu': {'message': None, 'error': None, 'status': True, 'data': {'cpu_count': 24, 'cpu_physical_count': 2, 'cpu_model': ' Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz'}},
            'os_version': 'CentOS release 6.777 (Final)',
            'main_board': {'message': None, 'error': None, 'status': True,
                           'data': {
                               'model': 'Parallels Virtual Platform',
                               'sn': 'Parallels-1A 1B CB 3B 64 66 4B 13 86 B0 86 FF 7E 2B 20 30',
                               'manufacturer': 'Parallels Software International Inc.'}},
            'disk': {'message': None, 'error': None, 'status': True,
                     'dat': {
                         '2': {'slot': '2', 'pd_type': 'SATA', 'model': 'SSD 850 PRO 512GB', 'capacity': '476.939'},
                         '3': {'slot': '3', 'pd_type': 'SATA', 'model': 'SSD 850 PRO 512GB', 'capacity': '476.939'},
                         '0': {'slot': '0', 'pd_type': 'SAS', 'model': 'SSD 850 PRO 512GB', 'capacity': '279.396'},
                         '1': {'slot': '1', 'pd_type': 'SAS', 'model': 'SSD 850 PRO 512GB', 'capacity': '279.396'},}},
            'memory': {'message': None, 'error': None, 'status': True,
                       'data': {
                           'DIMM #0': {'slot': 'DIMM #0', 'model': 'DRAM', 'sn': 'Not Specified', 'speed': '667 MHz', 'manufacturer': 'Not Specified', 'capacity': 0},
                           'DIMM #1': {'slot': 'DIMM #1', 'model': 'DRAM', 'sn': 'Not Specified', 'speed': '667 MHz', 'manufacturer': 'Not Specified', 'capacity': 0},
                           'DIMM #2': {'slot': 'DIMM #2', 'model': 'DRAM', 'sn': 'Not Specified', 'speed': '667 MHz', 'manufacturer': 'Not Specified', 'capacity': 0},
                           'DIMM #3': {'slot': 'DIMM #3', 'model': 'DRAM', 'sn': 'Not Specified', 'speed': '667 MHz', 'manufacturer': 'Not Specified', 'capacity': 0},}},
            'nic': {'message': None, 'error': None, 'status': True,
                    'data': {
                        'eth0': {
                            'ipaddrs': '10.211.55.4',
                            'netmask': '255.255.255.0',
                            'up': True,
                            'hwaddr': '00:1c:42:a5:57:7a'}}},
            },
    }
    import json
    ret = requests.post(
        url='http://127.0.0.1:8001/api/asset/',
        json=data_dict
    )
    # content-type: application/json

    # ret = requests.post(
    #     url='http://127.0.0.1:8000/api/asset3.html',
    #     data = data_dict
    # )
    # content-type: application/x-www-form-urlencoded
    print(ret.json())


if __name__ == '__main__':
    # god1()
    # god2()
    god3()