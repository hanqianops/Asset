from django.shortcuts import render, HttpResponse

import json
import importlib
from django.views import View
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator # 函数装饰器转换成方法装饰器

from utils import auth
from Asset import settings
from repository import models
from api.service import asset


class AssetView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AssetView, self).dispatch(request, *args, **kwargs)

    # @method_decorator(auth.api_auth)
    def get(self,  request, *args, **kwargs):
        """获取今日未更新的资产"""

        print("get====")
        response = asset.get_untreated_servers()
        return JsonResponse(response.__dict__)  # 返回json格式的数据

    # @method_decorator(auth.api_auth)
    def post(self, request, *args, **kwargs):
        """更新资产数据"""
        print("/api/asset/ POST: ",request.body)
        server_info = json.loads(request.body.decode('utf-8'))  # 把请求头中的内容转成json对象,b'{k1:v1,k2:v2}'
        server_info = server_info['data']
        hostname = server_info['hostname']
        ret = {'code': 1000, 'message': '[%s]更新完成' % hostname}

        server_obj = models.Server.objects.filter(hostname=hostname).select_related('asset').first()
        # server_obj.hostname = retail-gms-001
        # server_obj.asset.idc = xxx
        print("获取服务器对象==",server_obj)
        if not server_info:
            ret['code'] = 1002
            ret['message'] = '[%s]资产不存在' % hostname
            return  JsonResponse(ret)

        for k, v in settings.PLUGINS_DICT.items():
            module_path, cls_name = v.rsplit('.', 1)
            cls = getattr(importlib.import_module(module_path), cls_name)
            response = cls.process(server_obj, server_info, None)
            if not response.status:
                ret['code'] = 1003
                ret['message'] = "[%s]资产更新异常" % hostname
            if hasattr(cls, 'update_last_time'):
                cls.update_last_time(server_obj, None)
        return JsonResponse(ret)