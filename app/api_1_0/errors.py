# encoding:utf-8
'''
@author:lk

@time:2017/9/22 

@desc:

'''
from flask import jsonify

from app.api_1_0 import api
from app.exceptions import ValidationError

def bad_request(message):
    print('bad_request_api')
    response = jsonify({'error': '错误的请求', 'message': message})
    response.status_code = 400
    return response

def unauthorized(message):
    response = jsonify({'error': '未授权', 'message': message})
    response.status_code = 401
    return response

def forbidden(message):
    print('forbidden_api')
    response = jsonify({'error': '禁止访问', 'message': message})
    response.status_code = 403
    return response


# api蓝本路由视图抛出了异常才会调用这个处理程序,所有无需在视图函数上处理异常错误了
# 蓝本会自动调用该函数
@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])