import re
import unittest
from flask import url_for
from app import create_app, db
from app.modules import Role, User

# 测试web程序页面功能
class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 测试主页是否含有Default字段
    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue(b'Default' in response.data)

    # 测试注册和登录
    def test_register_and_login(self):
        # register a new account
        response = self.client.post(url_for('auth.register'), data={
            'email': '1743992140@qq.com',
            'username': 'test',
            'password': '111',
            'password2': '111'
        })
        self.assertTrue(response.status_code == 302) #是否注册成功后重定向到了main.index

        # login with the new account
        response = self.client.post(url_for('auth.login'), data={
            'email': '1743992140@qq.com',
            'password': '111'
        }, follow_redirects=True)
        self.assertTrue(re.search(b'Hello,\s+test!', response.data))
        self.assertTrue(
            b'您还没有确认您的账户哦' in response.data)

        # send a confirmation token
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue(
            b'您已经确认邮件成功,谢谢!' in response.data)

        # log out
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue(b'您的帐号已成功注销' in response.data)
