# encoding:utf-8
'''
@author:lk

@time:2017/9/8 

@desc:auth视图(登录)

'''
from flask import render_template, redirect, url_for, flash, request, session
from  flask_login import login_user, login_required, logout_user, current_user

from app import db
from app.email import send_email
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, PasswordResetForm, \
    PasswordResetRequestForm, ChangePasswordForm
from . import auth
from ..modules import User


# 登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # 定义一个文本字段和一个提交按钮
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()  # 从数据库查找email第一个用户,返回用户实例
        # 如果查询的数据存在且密码正确时
        if user is not None and user.verify_password(form.password.data):
            # session['known'] = True
            # 标记用户为已登录,remember_me问哦true时浏览器会写入一个长效的cookie,如果为false下次需重新登录
            # Flask_Login会把原地址保存在查询字符串的next参数中,这个参数可从request.args字典中读取,如果不存在就定位到首页
            #current_user会记住user对象
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        # else:
        #     session['known'] = False
        flash('帐号或密码错误.')
    return render_template('auth/login.html', form=form)


# 登出注销
# @login_required作用:表示这个Veiw需要登录认证,如果未认证的用户访问这个路由
# Flask-Login 会拦截请求，把用户发往登录页面。
#     用户登陆系统才可以访问某些页面
#     如果用户没有登陆而直接访问就会跳转到登陆界面，
#     用户在跳转的登陆界面中完成登陆后，自动访问跳转到之前访问的地址
@auth.route('/logout')
@login_required
def logout():
    # 登出账户,清除cookie信息
    logout_user()
    # session['known'] = False
    flash('您的帐号已成功注销')
    return redirect(url_for('main.index'))


# 用户注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # 判断表单的合法性
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        # 将user对象添加到数据库
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()  # 生成确认token链接
        send_email(user.email, '请确认您的账户', 'auth/email/confirm', user=user, token=token)
        flash('一封确认邮件已经发送到您的邮箱中了...')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


# 重新发送账户确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '请确认您的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认邮件已经发送到您的邮箱中了...')
    return redirect(url_for('main.index'))


# 确认邮件
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    # print(token)
    # print(current_user.confirmed)
    # print(current_user.confirm(token))
    # 如果当前用户已经确认过邮件就重定向到main.index界面,
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    # 如果token未失效提示需要邮件确认
    if current_user.confirm(token):
        flash('您已经确认邮件成功,谢谢!')
    else:
        flash('邮件确认链接已失效,请重试!')
    return redirect(url_for('main.index'))


# before_app_request和before_request都只能用在蓝本中,before_app_request是针对蓝本程序全局的,
# before_request只能应用到属于蓝本的请求上
# 每一次请求到来后，都会先执行它，如果没问题即没有执行到abort(400)，
# 那么就会进入到正常的被app.route修饰的函数中进行响应，
# 此处同时满足3个条件,before_app_request就会拦截请求:
#           1.用户已登录    2.用户的账户还未确定    3.请求的端点不在认证蓝本中
@auth.before_app_request
def before_request():
    # is_authenticated当用户通过验证时，也即提供有效证明时返回 True 。
    if current_user.is_authenticated:
        current_user.update_lastTime()  #更新最后访问的时间
        if not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    # is_anonymous返回是否是匿名用户, 也就是未登陆的用户
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

# 重置密码界面
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('您的密码已经重置成功.')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误.')
    return render_template("auth/change_password.html", form=form)

#重置密码请求界面
@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重置密码',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('一封请求重置密码的邮件已经发送到您邮箱了...')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

# 通过发送邮件来密码重置
@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('您的密码已经重置成功.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

#更换邮箱地址请求
@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, '确认您的邮箱',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('一封请求更换邮箱地址的邮件已经发送到您邮箱了...')
            return redirect(url_for('main.index'))
        else:
            flash('不合法的邮箱地址或密码.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('您的邮箱地址已经重置成功.')
    else:
        flash('不合法的请求.')
    return redirect(url_for('main.index'))

