# encoding:utf-8
'''
@author:lk

@time:2017/9/15 

@desc:检查用户权限的自定义装饰器

'''
from functools import wraps

from flask_login import current_user
from flask import abort, redirect, url_for, request

from app.modules import Permission, User


#decorator函数接受permission参数
def permission_required(permission):
    def decorator(f):
        #wraps的作用是将原始函数的__name__属性复制过来,也就是f.__name__不会在等于decorated_function,而是直接等于f的属性了
        @wraps(f)
        def decorated_function(*args,**kwargs):
            # 如果当前账户没有权限就显示403错误
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decorator

#管理员权限装饰器
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


#是否是当前用户装饰器
def isCurUser_required():
    id_name = request.path.split('/')[request.path.split('/').count()-1]
    print(id_name)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = User.query.filter_by(username=id_name).first()
            if current_user != user:
                user = User.query.filter_by(id=id).first()
                if current_user != user:
                    return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
