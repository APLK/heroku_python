# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:程序启动入口
    开发环境时,一定要先创建数据库,执行命令:
    db.create_all()
    Role.insert_roles()


    test测试代码
    python manage.py test

    利用coverage获取代码覆盖报告,用来统计单元测试检查
    了多少程序功能，并提供一个详细的报告，说明程序的哪些代码没有测试到
    python manage.py test --coverage

    创建数据库并插入一条语句
    python manage.py shell
    db.create_all()
    u=User(email='1399424199@qq.com',username='test',password='111')
    db.session.add(u)
    db.session.commit()

    数据库迁移命令(表结构发生改变时)
    python manage.py db init      (第一次才需要init,一旦存在migrations目录后就不需要这一步了)
    python manage.py db migrate
    python manage.py db upgrade

    创建需求文件 requirements.txt
    pip freeze >requirements.txt

    安装需求文件
    pip install -r requirements.txt

    分生产环境和开发环境下的需求文件
    pip freeze >requirements/common.txt

    创建100条用户和博客虚拟数据
    python manage.py shell
    User.generate_fake(70)
    Post.generate_fake(70)
    User.add_self_follows()
    Category.insert_categorys()

'''
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    # 函数 coverage.coverage() 用于启动覆盖检测引擎
    # branch=True 选项开启分支覆盖分析，
    # 除了跟踪哪行代码已经执行外，还要检查每个条件语句的 True 分支和 False 分支是否都执测试
    # include检查app下的所有目录
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import os
from app import create_app,db
from app.modules import User, Role, Post, Follow, Category
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand

app=create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
#数据库迁移
migrate = Migrate(app, db)
def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role,Post=Post,Follow=Follow,Category=Category) #将app,db,User,Role设置为全局变量,不需要引入直接就能调用
manager.add_command('shell',Shell(make_context=make_shell_context)) #使用shell命令调用make_context方法
manager.add_command('db',MigrateCommand) #使用db命令调用make_context方法

#单元测试调用
# coverage是否需要进行覆盖测试,false是不需要,否则需要
@manager.command
def test(coverage=False):
    """run the unit tests."""
    # 如果存在的话，则引入coverage功能，并开始覆盖率检查
    # 不过，正常开始时候，我们环境变量里面应该是没有这个变量值的
    # 所以，在下面的command命令test里面，他加入了参数用来添加环境变量
    # 并在添加完以后，重新执行当前文件，再次执行后，由于已经有环境变量了，所他会开始覆盖率检查
    # sys.executable表示的是当前python解释器的位置
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    tests = unittest.TestLoader().discover('tests') #测试所有tests目录下的py文件
    #0 (静默模式): 你只能获得总的测试用例数和总的结果 比如 总共100个 失败20 成功80
    #1 (默认模式): 非常类似静默模式 只是在每个成功的用例前面有个“.”  每个失败的用例前面有个 “F”
    #2 (详细模式):测试结果会显示每个测试用例的所有相关的信息
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
    COV.save()
    print('Coverage Summary:')
    COV.report()
    basedir = os.path.abspath(os.path.dirname(__file__))
    covdir = os.path.join(basedir, 'tmp/coverage')
    COV.html_report(directory=covdir)
    print('HTML version: file://%s/index.html' % covdir)
    COV.erase()

# python manage.py profile 启动程序后，终端会显示每条请求的分析数据，其中包
# 含运行最慢的 25 个函数
# profile_dir分析数据保存在指定的目录中
@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()

#调用此函数能自动创建数据库
@manager.command
def deploy():
    # python manage.py deploy
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.modules import Role, User

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

    # create self-follows for all users
    User.add_self_follows()
@manager.command
def delete_user():
    # python manage.py delete_user
    db.session.delete(User.query.filter_by(id=55).first())
    db.session.commit()

if __name__=='__main__':
    manager.run()
