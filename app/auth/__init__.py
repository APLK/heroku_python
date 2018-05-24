# encoding:utf-8
'''
@author:lk

@time:2017/9/8 

@desc:账户登录的蓝本

'''
from flask import Blueprint

auth = Blueprint('auth', __name__)
from . import views
