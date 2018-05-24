# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:程序工厂函数

'''
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_pagedown import PageDown

from config import config
from flask_login import LoginManager

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
# Flask-pagedown模块，将文本转换成html富文本数据，并在浏览器上显示，类似于博客文章的预览功能
pagedown = PageDown()
#可以设置为None,basic,strong,当为strong时,flask_login
#会记录客户端ip地址和浏览器的用户代理,发现登录异动就退出登录
login_manager.session_protection='strong'
#设置登录页面的端点
login_manager.login_view='auth.login'



# 程序的工厂函数,能留出配置程序的时间,还能创建多个app程序的事例,提高测试的覆盖率
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # 根据config中的key值决定初始化哪个

    # 初始化bootstrap,mail,moment,db,pagedown
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # with app.test_request_context():
    #     db.drop_all()
    #     db.create_all()
    # https加密设置
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint  # 导入main蓝本并注册到app程序上
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint  # 导入auth蓝本并注册到app程序上
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')  # 导入api蓝本并注册到app程序上
    return app
