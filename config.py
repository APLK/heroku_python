# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:flask配置文件

'''
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SERCET_KEY') or 'hard to guess string'  # 项目密钥
    MAIL_SERVER = 'smtp.163.com'  # 网易邮箱服务器
    MAIL_PORT = 25  # 网易邮箱端口号
    MAIL_USE_TLS = True  # 使用TLS
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''  # 登录平台用户名
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''  # 登录SMTP的授权码
    BOOTSTRAP_SERVE_LOCAL = True
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 表示每次request自动提交db.session.commit()
    # 视图函数只用写db.session.add(data),不用写db.session.commit()
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASKY_MAIL_SUBJECT_PREFIX = '[FLASKY]'  # 邮箱主题前面修饰前缀
    FLASKY_MAIL_SENDER = 'hwlk_90 <hwlk_90@163.com>'  # 收件箱中的发件人
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN') or 'hwlk_90@163.com'  # 发件人地址
    FLASKY_POSTS_PER_PAGE = 20  # 默认每页显示的数量
    FLASKY_FOLLOWERS_PER_PAGE = 50  # 默认粉丝列表或我的关注列表显示的数量
    FLASKY_COMMENTS_PER_PAGE = 15  # 默认评论列表显示的数量
    SQLALCHEMY_RECORD_QUERIES = True  # 启动缓慢查询记录功能
    FLASKY_SLOW_DB_QUERY_TIME = 0.5  # 数据库的查询时间
    SSL_DISABLE = True

    # 静态方法,可以通过实例变量或者类名直接调用
    @staticmethod
    def init_app(app):
        pass


# 开发配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data_dev.sqlite')  # 数据库位置

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 把生产模式中出现的错误通过电子邮件发送给 FLASKY_ADMIN 中设置的管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


# 测试配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data_test.sqlite')
    # Flask-WTF 生成的表单中包含一个隐藏字段，其内容是 CSRF 令牌，需要和表
    # 单中的数据一起提交。为了复现这个功能，测试必须请求包含表单的页面，然后解析响应
    # 返回的 HTML 代码并提取令牌，这样才能把令牌和表单中的数据一起发送。为了避免在测
    # 试中处理 CSRF 令牌这一烦琐操作，最好在测试配置中禁用 CSRF 保护功能
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # 处理代理服务器首部
        # ProxyFix 中间件添加在 Heroku 配置的初始化方法中。添加 ProxyFix 等 WSGI 中间件的方
        # 法是包装 WSGI 程序。收到请求时，中间件有机会审查环境，在处理请求之前做些修改。
        # 不仅 Heroku 需要使用 ProxyFix 中间件，任何使用反向代理的部署环境都需要。
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log日志记录
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}
