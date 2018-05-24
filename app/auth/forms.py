# encoding:utf-8
'''
@author:lk

@time:2017/9/8 

@desc:auth的登录表单

'''
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError

from app.modules import User


class LoginForm(FlaskForm):
    # DataRequired 检查类型转换后的值，是否为真,Email验证邮箱格式
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])  # 属性为type='password'的<input>元素
    remember_me = BooleanField('记住我的登录状态')  # 复选框
    submit = SubmitField('登录')


# 此处继承FlaskForm类,否则会提示警告
# "flask_wtf.Form" has been renamed to "FlaskForm" and will be removed in 1.0.
class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()]) \
        # Regexp正则匹配用户名格式
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     '用户名只能是字母,数字或下划线组成')])
    password = PasswordField('密码',
                             validators=[DataRequired(),
                                         EqualTo('password2', message='两次输入的密码必须一致')])
    password2 = PasswordField('确认密码',
                              validators=[DataRequired()])
    submit = SubmitField('注册')

    # 如果表单类中定义了以
    # validate_ 开头且后面跟着字段名的方法，这个方法就和常规的验证函数一起调用
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱地址已经被注册过了!')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在!')

#更改密码
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码必须一致')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('更新密码')

#密码重置请求
class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('发送邮件')

#通过发送邮件来密码重置
class PasswordResetForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码必须一致')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('未知的邮箱地址.')

#邮箱地址更换
class ChangeEmailForm(FlaskForm):
    email = StringField('新的邮箱地址', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('更新邮箱地址')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱地址已经被注册过了!')