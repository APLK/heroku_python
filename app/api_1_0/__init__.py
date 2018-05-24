# encoding:utf-8
'''
@author:lk

@time:2017/9/22 

@desc:创建一个 REST Web 服务，以便让客户端访问博客文章
及相关资源

'''
from flask import Blueprint
#第一个参数蓝本的名字,参数二是蓝本所在的包或模块
api = Blueprint('api', __name__)

#因为在views.py和error.py中也要导入蓝本main,这样可以避免循环导入依赖
from . import errors,posts,authentication,users


# (venv) $ http --json --auth <email>:<password> GET \
# > http://127.0.0.1:5000/api/v1.0/posts
# 示例: http --json --auth 1399424199@qq.com:111 GET http://127.0.0.1:5000/api/v1.0/posts/
#       http --json --auth : GET http://127.0.0.1:5000/api/v1.0/posts/


# 发送 POST 请求以添加一篇新博客文章：
# (venv) $ http --auth 1399424199@qq.com:111 --json POST \
#  http://127.0.0.1:5000/api/v1.0/posts/ \
#  "body=测试博客api新增功能"

# http --auth 1399424199@qq.com:111 --json GET http://127.0.0.1:5000/api/v1.0/token
