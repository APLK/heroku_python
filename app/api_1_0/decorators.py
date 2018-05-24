from functools import wraps
from flask import g

from .errors import forbidden

# 权限装饰器
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                #如果是abort(403)就会被main蓝本中的@main.app_errorhandler(403)捕捉,此处表示api这个蓝本自己
                #处理,直接响应自己定义的forbidden函数
                return forbidden('权限不够!')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

