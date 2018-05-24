import re
import threading
import time
import unittest
from selenium import webdriver
from app import create_app, db
from app.modules import Role, User, Post

#Selenium进行客户端自动化测试
class SeleniumTestCase(unittest.TestCase):
    client = None
    # ① setup():每个测试函数运行前运行
    # ② teardown():每个测试函数运行完后执行
    # ③ setUpClass():必须使用@classmethod 装饰器,所有test运行前运行一次
    # ④ tearDownClass():必须使用@classmethod装饰器,所有test运行完后运行一次
    @classmethod
    def setUpClass(cls):
        # start Firefox
        try:
            cls.client = webdriver.Firefox()
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            # add an administrator user
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='john@example.com',
                         username='john', password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # start the Flask server in a thread
            threading.Thread(target=cls.app.run).start()

            # give the server a second to ensure it is up
            time.sleep(1) 

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the flask server and the browser
            # 测试完成之后调用main蓝本中的shutdown端点路径关闭selenium客户端
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            # destroy database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('浏览器不支持')

    def tearDown(self):
        pass
    
    def test_admin_home_page(self):
        # navigate to home page
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,\s+请登录!',
                                  self.client.page_source))

        # navigate to login page
        self.client.find_element_by_link_text('登录').click()
        self.assertTrue('<h1>登录</h1>' in self.client.page_source)

        # login
        self.client.find_element_by_name('邮箱').\
            send_keys('john@example.com')
        self.client.find_element_by_name('密码').send_keys('cat')
        self.client.find_element_by_name('登录').click()
        self.assertTrue(re.search('Hello,\s+john!', self.client.page_source))

        # navigate to the user's profile page
        self.client.find_element_by_link_text('个人资料').click()
        self.assertTrue('<h1>john</h1>' in self.client.page_source)
