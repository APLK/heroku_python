# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:单元测试
test类自定义的方法都是以test开头的
每个测试类都必须重写setUp和tearDown方法

'''
import unittest
from flask import current_app
from app import create_app, db
from app.modules import Role


class BasicTestCase(unittest.TestCase):
    # TestCase的方法,测试前运行
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    # TestCase的方法,测试后运行
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 测试app是否存在
    def test_app_exists(self):
        self.assertFalse(current_app is None)

    # 测试app是否正在测试环境
    def test_app_is_testing(self):
        self.assertTrue(
            current_app.config['TESTING'])  # TESTING是config.py TestingConfig的TESTING=True
