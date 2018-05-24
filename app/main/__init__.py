# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:main蓝本

'''
from flask import Blueprint
#第一个参数蓝本的名字,参数二是蓝本所在的包或模块
from app.modules import Permission

main = Blueprint('main', __name__)

#因为在views.py和error.py中也要导入蓝本main,这样可以避免循环导入依赖
from . import views,errors

#注解一个Permission模版参数,便于每次调用render_template()来渲染html页面时时多添加一个Permission参数
# Permission参数能够在程序所有模板中全局访问
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
