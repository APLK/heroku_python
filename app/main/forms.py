# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:表单样式

'''
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, ValidationError

#表单类，定义了一个文本字段和一个提交按钮
#DataRequired()为验证函数
from app.modules import Role, User, Category


#表单类，定义了普通用户资料编辑的表单
class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('所属地', validators=[Length(0, 64)])
    about_me = TextAreaField('自我描述')
    submit = SubmitField('提交')

#表单类,定义一个管理员使用的资料编辑表单
class EditProfileAdminForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64),
                                           Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                  '用户名只能是字母,数字或下划线组成')])
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    confirmed = BooleanField('确认状态')
    role = SelectField('选择权限', coerce=int)
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('所属地', validators=[Length(0, 64)])
    about_me = TextAreaField('自我描述')
    submit = SubmitField('提交')

    #初始化SelectField的数据,从roles表中按角色名的字母排序查询所有的数据,填充到SelectField数据中
    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        #choices必须是一个元组组成的列表(选项的标识符,显示在空间中的文本字符串),应为标识符是角色的id,所以
        #SelectField的coerce为int类型
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user=user

    def validate_username(self,field):
        if field.data!=self.user.username and \
            User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在!')

    def validate_email(self,field):
        if field.data!=self.user.email and \
            User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册过了')

# 定义一个博客编辑表单
class PostForm(FlaskForm):
    category = SelectField('博客分类', coerce=int)
    title = StringField('博客标题', validators=[DataRequired()])
    body = PageDownField('博客内容', validators=[DataRequired()])
    submit = SubmitField('发表')
    #初始化SelectField的数据,从roles表中按角色名的字母排序查询所有的数据,填充到SelectField数据中
    def __init__(self,*args,**kwargs):
        super(PostForm,self).__init__(*args,**kwargs)
        #choices必须是一个元组组成的列表(选项的标识符,显示在空间中的文本字符串),应为标识符是角色的id,所以
        #SelectField的coerce为int类型
        self.category.choices = [(category.id, category.name)
                             for category in Category.query.all()]

#评论编辑表单
class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('提交')







