# encoding:utf-8
'''
@author:lk

@time:2017/9/22 

@desc:身份认证

'''
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from app.api_1_0 import api
from app.api_1_0.errors import unauthorized, forbidden
from app.modules import AnonymousUser, User

auth = HTTPBasicAuth()

#最先执行该方法,其次才会执行before_request
# 验证邮箱及密码(也可以通过token进行登录认证)
@auth.verify_password
def verify_password(email_or_token, password):
    print(email_or_token+","+password)
    if email_or_token == '':
        g.current_user = AnonymousUser()  #匿名用户,即游客
        return True
    if password=='':
        # 验证token
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used=True
        return g.current_user is not None
    #邮箱和密码验证
    user = User.query.filter_by(email = email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used=False
    return user.verify_password(password)

# Flask-HTTPAuth 错误处理程序
@auth.error_handler
def auth_error():
    return unauthorized('无效凭证')

# 每次请求之前先通过login_required装饰器过滤掉未登录的用户,然后才放行
@api.before_request
@auth.login_required
def before_request():
    print('before_request')
    #如果当前的账户不是匿名的并且还未认证过
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('暂未认证的账户')

# 生成token
@api.route('/token')
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('暂未认证的账户')
    # 视图函数返回 JSON 格式的响应，其中
    # 包含了过期时间为 1 小时的令牌
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
