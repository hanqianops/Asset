# coding: utf-8
__author__ = "HanQian"
import traceback
import datetime
from utils.response import BaseResponse
from utils import agorithm
from repository import models

from django.db.models import Q
import datetime


def get_untreated_servers():
    """获取今日未采集信息的主机"""
    response = BaseResponse()
    try:
        current_date = datetime.date.today()
        condition = Q()

        # 今日未采集的资产
        con_date = Q()
        con_date.connector = 'OR'
        con_date.children.append(("asset__latest_date__lt", current_date))
        con_date.children.append(("asset__latest_date", None))

        # 在线状态的服务器
        con_status = Q()
        con_status.children.append(('asset__device_status_id', '2'))

        result = models.Server.objects.filter(condition).values('hostname')
        response.data = list(result)
        response.status = True

    except Exception as e:
        response.message = str(e)
        models.ErrorLog.objects.create(
            asset_obj=None,
            title='获取今日未采集信息的服务器出错',
            content=traceback.format_exc()
        )
    return response


class HandleBasic(object):
    """处理系统基本信息,并记录日志"""

    @staticmethod
    def process(server_obj, server_info, user_obj):
        """
        :param server_obj:  服务器的当前信息
        :param server_info: 采集到的信息
        :param user_obj: 用户对象
        :return:
        """
        response = BaseResponse()
        try:
            log_list = []
            main_board = server_info['main_board']['data']
            cpu = server_info['cpu']['data']
            if server_obj.os_platform != server_info['os_platform']:
                log_list.append('系统由%s变更为%s' % (server_obj.os_platform, server_info['os_platform'],))
                server_obj.os_platform = server_info['os_platform']

            if server_obj.os_version != server_info['os_version']:
                log_list.append(u'系统版本由%s变更为%s' % (server_obj.os_version, server_info['os_version'],))
                server_obj.os_version = server_info['os_version']

            if server_obj.sn != main_board['sn']:
                log_list.append(u'主板SN号由%s变更为%s' % (server_obj.sn, main_board['sn'],))
                server_obj.sn = main_board['sn']

            if server_obj.manufacturer != main_board['manufacturer']:
                log_list.append(u'主板厂商由%s变更为%s' % (server_obj.manufacturer, main_board['manufacturer'],))
                server_obj.manufacturer = main_board['manufacturer']

            if server_obj.model != main_board['model']:
                log_list.append(u'主板型号由%s变更为%s' % (server_obj.model, main_board['model'],))
                server_obj.model = main_board['model']

            if server_obj.cpu_count != cpu['cpu_count']:
                log_list.append(u'CPU逻辑核数由%s变更为%s' % (server_obj.cpu_count, cpu['cpu_count'],))
                server_obj.cpu_count = cpu['cpu_count']

            if server_obj.cpu_physical_count != cpu['cpu_physical_count']:
                log_list.append(
                    u'CPU物理核数由%s变更为%s' % (server_obj.cpu_physical_count, cpu['cpu_physical_count'],))
                server_obj.cpu_physical_count = cpu['cpu_physical_count']

            if server_obj.cpu_model != cpu['cpu_model']:
                log_list.append(u'CPU型号由%s变更为%s' % (server_obj.cpu_model, cpu['cpu_model'],))
                server_obj.cpu_model = cpu['cpu_model']
            server_obj.save()

            # 记录变更日志
            if log_list:
                models.AssetRecord.objects.create(asset_obj=server_obj.asset,
                                                  creator=user_obj,
                                                  content=';'.join(log_list))
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                           title='basic-run',
                                           content=traceback.format_exc())
        return response

    @staticmethod
    def update_last_time(server_obj, user_obj):
        """
        更新采集时间
        :param server_obj:
        :param user_obj:
        :return:
        """
        response = BaseResponse()
        try:
            current_date = datetime.date.today()
            server_obj.asset.latest_date = current_date
            server_obj.asset.save()
            models.AssetRecord.objects.create(asset_obj=server_obj.asset,
                                              creator=user_obj,
                                              content='资产汇报')
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                           title='更新采集时间失败',
                                           content=traceback.format_exc())

        return response


class HandleNic(object):
    """处理网卡信息, 并记录日志"""
    @staticmethod
    def process(server_obj, server_info, user_obj):
        """
        :param server_obj:  当前的服务器对象
        :param server_info: agent上报的信息
        :param user_obj: 用户对象
        :return:
        """
        response = BaseResponse()
        try:
            nic_info = server_info['nic']
            if not nic_info['status']:
                response.status = False
                models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                               title='采集网卡信息错误',
                                               content=nic_info['error'])
                return response

            client_nic_dict = nic_info['data']  # 新采集的数据
            nic_obj_list = models.NIC.objects.filter(server_obj=server_obj)         # 当前数据库中网卡对象列表
            nic_name_list = map(lambda x: x, (item.name for item in nic_obj_list))  # 当前数据库中每个网卡的名字列表

            update_list = set(client_nic_dict.keys()) & set(nic_name_list)  # 并集列表， 需要更新的
            add_list = set(client_nic_dict.keys()) - set(nic_name_list) # 差集列表， 需要增加的
            del_list = set(nic_name_list) - set(client_nic_dict.keys())  # 差集列表， 需要删除的

            HandleNic._add_nic(add_list, client_nic_dict, server_obj, user_obj)
            HandleNic._update_nic(update_list, nic_obj_list, client_nic_dict, server_obj, user_obj)
            HandleNic._del_nic(del_list, nic_obj_list, server_obj, user_obj)
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                           title='网卡信息变更失败',
                                           content=traceback.format_exc())

        return response

    @staticmethod
    def _add_nic(add_list, client_nic_dict, server_obj, user_obj):
        """添加新网卡"""
        for item in add_list:
            cur_nic_dict = client_nic_dict[item]  # 当前的某一条网卡信息
            cur_nic_dict['name'] = item          # 当前的网卡名字
            log_str = '[新增网卡]{name}:mac地址为{hwaddr};状态为{up};掩码为{netmask};IP地址为{ipaddrs}'.format(**cur_nic_dict)
            cur_nic_dict['server_obj'] = server_obj   # 当前网卡属于哪个服务器
            models.NIC.objects.create(**cur_nic_dict)  # 写入数据库
            models.AssetRecord.objects.create(asset_obj=server_obj.asset,   # 记录变更信息
                                              creator=user_obj,
                                              content=log_str)

    @staticmethod
    def _del_nic(del_list, nic_obj_list, server_obj, user_obj):
        """
        删除网卡
        """
        for item in nic_obj_list:
            if item.name in del_list:
                item.delete()
                log_str = '[移除网卡]{name}:mac地址为{hwaddr};状态为{up};掩码为{netmask};IP地址为{ipaddrs}'.format(**item.__dict__)
                models.AssetRecord.objects.create(asset_obj=server_obj.asset,
                                                  creator=user_obj,
                                                  content=log_str)

    @staticmethod
    def _update_nic(update_list, nic_obj_list, client_nic_dict, server_obj, user_obj):
        """更新网卡信息"""
        for item in nic_obj_list:
            if item.name in update_list:
                log_list = []

                new_hwaddr = client_nic_dict[item.name]['hwaddr']
                if item.hwaddr != new_hwaddr:
                    log_list.append(u"[更新网卡]%s:mac地址由%s变更为%s" % (item.name, item.hwaddr, new_hwaddr))
                    item.hwaddr = new_hwaddr
                new_up = client_nic_dict[item.name]['up']
                if item.up != new_up:
                    log_list.append(u"[更新网卡]%s:状态由%s变更为%s" % (item.name, item.up, new_up))
                    item.up = new_up

                new_netmask = client_nic_dict[item.name]['netmask']
                if item.netmask != new_netmask:
                    log_list.append(u"[更新网卡]%s:掩码由%s变更为%s" % (item.name, item.netmask, new_netmask))
                    item.netmask = new_netmask

                new_ipaddrs = client_nic_dict[item.name]['ipaddrs']
                if item.ipaddrs != new_ipaddrs:
                    log_list.append(u"[更新网卡]%s:IP地址由%s变更为%s" % (item.name, item.ipaddrs, new_ipaddrs))
                    item.ipaddrs = new_ipaddrs

                item.save()
                if log_list:
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset,
                                                      creator=user_obj,
                                                      content=';'.join(log_list))


class HandleMemory(object):
    """处理内存信息， 并记录日志"""

    @staticmethod
    def process(server_obj, server_info, user_obj):
        response = BaseResponse()
        try:
            mem_info = server_info['memory']
            if not mem_info['status']:
                models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                               title='采集内存信息错误',
                                               content=mem_info['error'])
                response.status = False
                return response

            client_mem_dict = mem_info['data']  # # 新采集的内存数据
            mem_obj_list = models.Memory.objects.filter(server_obj=server_obj)   # 当前数据库中内存对象列表
            mem_slots = map(lambda x: x, (item.slot for item in mem_obj_list))   # # 当前数据库中每个内存条的名字列表

            update_list = set(client_mem_dict.keys()) & set(mem_slots)  # 并集列表， 需要更新的
            add_list = set(client_mem_dict.keys()) - set(mem_slots)  # 差集列表， 需要增加的
            del_list = set(mem_slots) - set(client_mem_dict.keys())  # 差集列表， 需要删除的

            HandleMemory._add_memory(add_list, client_mem_dict, server_obj, user_obj)
            HandleMemory._update_memory(update_list, mem_obj_list, client_mem_dict, server_obj, user_obj)
            HandleMemory._del_memory(del_list, mem_obj_list, server_obj, user_obj)
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                           title='更新内存信息失败',
                                           content=traceback.format_exc())

        return response

    @staticmethod
    def _add_memory(add_list, client_mem_dict, server_obj, user_obj):
        for item in add_list:
            cur_mem_dict = client_mem_dict[item]
            log_str = '[新增内存]插槽为{slot};容量为{capacity};类型为{model};速度为{speed};厂商为{manufacturer};SN号为{sn}'.format(
                **cur_mem_dict)
            cur_mem_dict['server_obj'] = server_obj
            models.Memory.objects.create(**cur_mem_dict)
            models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _del_memory(del_list, mem_objs, server_obj, user_obj):
        for item in mem_objs:
            if item.slot in del_list:
                log_str = '[移除内存]插槽为{slot};容量为{capacity};类型为{model};速度为{speed};厂商为{manufacturer};SN号为{sn}'.format(
                    **item.__dict__)
                item.delete()
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _update_memory(update_list, mem_objs, client_mem_dict, server_obj, user_obj):
        for item in mem_objs:
            if item.slot in update_list:
                log_list = []

                new_manufacturer = client_mem_dict[item.slot]['manufacturer']
                if item.manufacturer != new_manufacturer:
                    log_list.append(u"[更新内存]%s:厂商由%s变更为%s" % (item.slot, item.manufacturer, new_manufacturer))
                    item.manufacturer = new_manufacturer

                new_model = client_mem_dict[item.slot]['model']
                if item.model != new_model:
                    log_list.append(u"[更新内存]%s:型号由%s变更为%s" % (item.slot, item.model, new_model))
                    item.model = new_model

                new_capacity = client_mem_dict[item.slot]['capacity']
                if item.capacity != new_capacity:
                    log_list.append(u"[更新内存]%s:容量由%s变更为%s" % (item.slot, item.capacity, new_capacity))
                    item.capacity = new_capacity

                new_sn = client_mem_dict[item.slot]['sn']
                if item.sn != new_sn:
                    log_list.append(u"[更新内存]%s:SN号由%s变更为%s" % (item.slot, item.sn, new_sn))
                    item.sn = new_sn

                new_speed = client_mem_dict[item.slot]['speed']
                if item.speed != new_speed:
                    log_list.append(u"[更新内存]%s:速度由%s变更为%s" % (item.slot, item.speed, new_speed))
                    item.speed = new_speed

                item.save()
                if log_list:
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                      content=';'.join(log_list))


class HandleDisk(object):
    @staticmethod
    def process(server_obj, server_info, user_obj):
        response = BaseResponse()
        try:
            disk_info = server_info['disk']
            if not disk_info['status']:
                response.status = False
                models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                               title='采集硬盘信息失败',
                                               content=disk_info['error'])
                return response

            client_disk_dict = disk_info['data']
            disk_obj_list = models.Disk.objects.filter(server_obj=server_obj)
            disk_slots = map(lambda x: x, (item.slot for item in disk_obj_list))

            update_list = set(client_disk_dict.keys()) & set(disk_slots)  # 并集列表， 需要更新的
            add_list = set(client_disk_dict.keys()) - set(disk_slots)  # 差集列表， 需要增加的
            del_list = set(disk_slots) - set(client_disk_dict.keys())  # 差集列表， 需要删除的

            HandleDisk._add_disk(add_list, client_disk_dict, server_obj, user_obj)
            HandleDisk._update_disk(update_list, disk_obj_list, client_disk_dict, server_obj, user_obj)
            HandleDisk._del_disk(del_list, disk_obj_list, server_obj, user_obj)

        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset,
                                           title='更新硬盘信息失败',
                                           content=traceback.format_exc())
        return response


    @staticmethod
    def _add_disk(add_list, client_disk_dict, server_obj, user_obj):
        for item in add_list:
            cur_disk_dict = client_disk_dict[item]
            log_str = '[新增硬盘]插槽为{slot};容量为{capacity};硬盘类型为{pd_type};型号为{model}'.format(**cur_disk_dict)
            cur_disk_dict['server_obj'] = server_obj
            models.Disk.objects.create(**cur_disk_dict)
            models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _del_disk(del_list, disk_objs, server_obj, user_obj):
        for item in disk_objs:
            if item.slot in del_list:
                log_str = '[移除硬盘]插槽为{slot};容量为{capacity};硬盘类型为{pd_type};型号为{model}'.format(**item.__dict__)
                item.delete()
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _update_disk(update_list, disk_objs, client_disk_dict, server_obj, user_obj):
        for item in disk_objs:
            if item.slot in update_list:
                log_list = []

                new_model = client_disk_dict[item.slot]['model']
                if item.model != new_model:
                    log_list.append(u"[更新硬盘]插槽为%s:型号由%s变更为%s" % (item.slot, item.model, new_model))
                    item.model = new_model

                new_capacity = client_disk_dict[item.slot]['capacity']
                new_capacity = float(new_capacity)
                if item.capacity != new_capacity:
                    log_list.append(u"[更新硬盘]插槽为%s:容量由%s变更为%s" % (item.slot, item.capacity, new_capacity))
                    item.capacity = new_capacity

                new_pd_type = client_disk_dict[item.slot]['pd_type']
                if item.pd_type != new_pd_type:
                    log_list.append(u"[更新硬盘]插槽为%s:硬盘类型由%s变更为%s" % (item.slot, item.pd_type, new_pd_type))
                    item.pd_type = new_pd_type

                item.save()
                if log_list:
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                      content=';'.join(log_list))