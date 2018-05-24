# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:错误视图

'''
from flask import render_template, request, jsonify
from  . import main

#403禁止访问
#如果使用errorhandler装饰器,那么只有该main蓝本中的错误才会触发错误视图,app_errorhandler能全局错误触发
@main.app_errorhandler(403)
def forbidden(e):
    print('forbidden')
    #请求头部accept_mimetypes,客户端接受json的响应格式accept_json
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': '禁止访问'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403

#404页面不存在
@main.app_errorhandler(404)
def page_not_found(e):
    print('page_not_found')
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': '页面地址不存在'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404

#500服务器异常
@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': '服务器异常'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500