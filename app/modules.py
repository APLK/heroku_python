# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:

'''
import hashlib

import bleach
import re
from flask import current_app, request, url_for, flash, session
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
from pymysql import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from app import db
from app.exceptions import ValidationError
from . import login_manager
from datetime import datetime


# 关注表(每一行都表示一个用户关注另一个用户)
# 主动关注者id： follower_id
# 被关注者的id： followed_id
# 左边关注右边
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)


# 用户表
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # 主键primary_key 等价于 唯一 (UNIQUE) 且 非空 (NOT NULL)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)  # 邮箱
    username = db.Column(db.String(64), unique=True, index=True)  # 用户名
    # 注册时邮件注册的确认链接是否已确认
    confirmed = db.Column(db.Boolean, default=False)
    # 密码散列值
    password_hash = db.Column(db.String(128))  # 密码散列值
    # 外键role_id对应roles.id
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    name = db.Column(db.String(64))  # 真实姓名
    location = db.Column(db.String(64))  # 所在地
    about_me = db.Column(db.Text())  # 自我介绍
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # 注册时间
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)  # 最后访问时间
    avatar_hash = db.Column(db.String(32))  # gravatat中的图像hash地址值
    # lazy有三个属性值:
    #    select就是访问到属性的时候，就会全部加载该属性的数据。
    #    joined则是在对关联的两个表进行join操作，从而获取到所有相关的对象。
    #    dynamic则不一样，在访问属性的时候，并没有在内存中加载数据，而是返回一个query对象, 需要执行相应方法才可以获取对象，比如.all()
    # 定义一个反向引用，Post可以通过author查询到User的集合
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    # followers表示自己的粉丝，对应的是Follow类里面的followed_id，这个有点拗口，这个其实是自己粉丝的id
    # followed表示已经关注的人，他对应的是Follow类里面的follower_id这个属性，也就是，关注了哪些人，具体的值是id号
    # 将多对多的关系分拆成两个一对多的关系,db.backref是回引Follow模型
    # cascade的all表示自动把所有关系的对象添加到会话中,delete-orphan表示删除记录后把指向该记录的实体也一起删除了

    # followed:
    # 如果要通过用户id找到该用户主动关注的所有用户需要先从用户id和follows表间的一对多关系开始,获取这个用户id
    # 在follows表中所有的记录,然后再按照多到一的方向遍历被关注对象中和follows表之间的一对多的关系 ,
    # 找到这位用户id在follows表中的各记录所对应的被关注对象(左边关注右边,左边是主动关注对象follower_id,右边是被关注对象followed_id)
    # followers:
    # 同理,若想找到某个关注了该用户id的所有主动关注者,获取这个用户的id在所有的记录,再获取这些记录联接的主动关注者
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],  # 对应的是follows表中的followed_id字段
                                # 定义一个反向引用的回引，Follow可以通过followed查询到User的集合
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic', cascade='all,delete-orphan')
    # 将多对多的关系分拆成两个一对多的关系,db.backref是回引Follow模型
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],  # 对应的是follows表中的follower_id字段
                               # 定义一个反向引用的回引，Follow可以通过follower查询到User的集合
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all,delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # 此处是判断该用户是否是管理员邮箱注册的,如果是就将该用户设置为管理员权限,如果不是就将该用户设置为普通的用户权限
        if self.role is None:
            # 如果用户邮箱等于发件人的邮箱地址,就将查询role表中权限为所有权0xff的角色置为该用户的角色
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            # 否则就将role表中default为True的User角色权限置为该用户的角色
            else:
                self.role = Role.query.filter_by(default=True).first()
        # 如果邮件地址存在并且头像hash地址不存在时就生成一个hash值
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.follow(self)

    # 添加自己关注自己
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # 删除用户
    def deleteUser(self, user):
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False
        return False
        # 手动把Follow实例插入关联表中,从而实现我关注的人followed和关注我的人followed链接起来

    def follow(self, user):
        # 如果被我关注的列表中不存在该用户就添加
        if not self.is_following(user):
            f = Follow(followed=user, follower=self)  # followed被关注者,follower粉丝
            db.session.add(f)

    # 取消我关注的他
    def unfollow(self, user):
        # 查询被我关注的列表中存在该用户,就将该条数据删除
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    # 如果被我关注的列表中存在user.id就返回True,否则false
    def is_following(self, user):
        # 在followed查找被关注的对象followed_id是否存在
        # print(self.followed.count())
        return self.followed.filter_by(followed_id=user.id).first() is not None

    # 如果主动关注列表中该user.id存在就返回True,否则false
    def is_followed_by(self, user):
        # 在followers查找主动关注对象中follower_id是否存在
        return self.followers.filter_by(follower_id=user.id).first() is not None

    # followed_posts定义为property时,调用时不用加()
    @property
    def followed_posts(self):
        # return db.session.query(Post).select_from(Follow).filter_by(follower_id=self.id).\
        # join(Post, Follow.followed_id == Post.author_id)
        # 你在此之前见到的查询都是从所查询模型的query属性开始的。这种查询不能在这里使用，
        # 因为查询要返回 posts 记录，所以首先要做的操作是在follows表上执行过滤器。因此，
        # 这里使用了一种更基础的查询方式。为了完全理解上述查询下面分别说明各部分：
        #     • db.session.query(Post)指明这个查询要返回Post对象；
        #     • select_from(Follow)的意思是这个查询从Follow模型开始；
        #     • filter_by(follower_id=self.id)使用关注用户过滤follows表；
        #     • join(Post, Follow.followed_id == Post.author_id) 联结filter_by()得到的结果和Post对象。
        # 调换过滤器和联结的顺序可以简化这个查询
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)

    def followed_category_posts(self,id):
        # return db.session.query(Post).select_from(Follow).filter_by(follower_id=self.id).\
        # join(Post, Follow.followed_id == Post.author_id)
        # 你在此之前见到的查询都是从所查询模型的query属性开始的。这种查询不能在这里使用，
        # 因为查询要返回 posts 记录，所以首先要做的操作是在follows表上执行过滤器。因此，
        # 这里使用了一种更基础的查询方式。为了完全理解上述查询下面分别说明各部分：
        #     • db.session.query(Post)指明这个查询要返回Post对象；
        #     • select_from(Follow)的意思是这个查询从Follow模型开始；
        #     • filter_by(follower_id=self.id)使用关注用户过滤follows表；
        #     • join(Post, Follow.followed_id == Post.author_id) 联结filter_by()得到的结果和Post对象。
        # 调换过滤器和联结的顺序可以简化这个查询
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id).filter(Post.category_id==id)

    # 生成模拟的虚拟用户数据100条
    @staticmethod
    def generate_fake(count=100):
        from random import seed
        from sqlalchemy.exc import IntegrityError
        import forgery_py
        # seed()使用相同的种子，则产生的随机数是相同的
        seed()
        for i in range(count):
            user = User(email=forgery_py.internet.email_address(),  # 邮箱地址
                        username=forgery_py.internet.user_name(True),  # 带数字拼接的username
                        password=forgery_py.lorem_ipsum.word(),
                        confirmed=True,
                        name=forgery_py.name.full_name(),
                        location=forgery_py.address.city(),
                        about_me=forgery_py.lorem_ipsum.sentence(),
                        member_since=forgery_py.date.date(True))
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                print('IntegrityError')
                db.session.rollback()  # 就是数据库里做修改后未commit之前使用rollback可以恢复数据到修改之前

    # 计算密码散列值的函数通过名为password的只写属性实现
    # @property，在对实例属性操作的时候，就知道该属性很可能不是直接暴露的，而是通过getter和setter方法来实现的。
    # 还可以定义只读属性，只定义getter方法，不定义setter方法就是一个只读属性：
    @property
    def password(self):
        raise AttributeError('password is not readable attribute')

    # password写属性
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 验证散列密码
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 邮件确认,Serializer会生成有效期一小时的token,
    # dumps方法为指定的数据生成一个加密签名,loads方法检验签名和过期时间
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception as e:
            print(e.message)
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    # 判断用户的权限是否存在
    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    # 判断用户的权限是否是管理员的权限
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 更新用户最后访问的时间
    def update_lastTime(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    # gravatar头像
    # 上过stackoverflow或者github的都知道，他们的默认头像，都是类似与大块像素一样的默认头像，
    # 其实，这个是通过一个叫做gravatar的全球统一头像服务网站进行设置的
    # 你在这个网站上可以通过将email和头像绑定，以后只要在支持gravatar功能的网站上使用这个email注册账号，
    # 那么头像就自动变成你已经绑定的头像了
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'https://www.gravatar.com/avatar'
        # 通过电子邮件地址生成的唯一md5图片参数
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        # s图片大小,d没有注册gravatar服务的使用默认图片生成方式,r图片级别
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    # dumps方法为指定的数据生成一个邮件地址更换加密签名,loads方法检验签名和过期时间
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    # 通过改变邮件地址来改变头像地址的hash值
    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        # 如果新的邮件地址存在返回false,邮件已经被注册,必须是未注册的邮件地址
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    # 生成一个身份token
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    # 验证身份的token信息,根据token的id字段返回用户信息
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    # 从json中获取body字段
    @staticmethod
    def from_json(json_post):
        print(json_post)
        email = json_post.get('email')
        if email is None or email == '':
            raise ValidationError('邮箱地址不存在!')
        str = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
        if re.match(str, email):
            print(email)
            if User.query.filter_by(email=email).first() is not None:
                return User.query.filter_by(email=email).first()
            else:
                ValidationError('邮箱地址不存在!')
        else:
            raise ValidationError('邮箱地址不合法!')

    # User的json数据
    def to_json(self):
        json_user = {
            'url': url_for('api.get_post', id=self.id, _external=True),  # 完整的api的url地址
            'username': self.username,  # 用户名
            'member_since': self.member_since,  # 注册时间
            'last_seen': self.last_seen,  # 最后一次登录时间
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),  # 用户博客api地址
            'followed_posts': url_for('api.get_user_followed_posts',
                                      id=self.id, _external=True),  # 用户好友博客的api地址
            'post_count': self.posts.count()  # 博客数
        }
        return json_user


# 用户角色权限表
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 是否为默认角色
    permissions = db.Column(db.Integer)  # 操作权限
    # User对象通过backref的role来设置用户的角色,例如ser_john = User(username='john', role=Role(name='User'))
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        # 定义三个权限角色,并添加到数据库
        # User是默认角色
        roles = {
            'User': (
                Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
            'Moderator': (
                Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS,
                False),
            'Administrator': (
                0xff, False)
        }
        for key in roles:
            role = Role.query.filter_by(name=key).first()
            if role is None:
                role = Role(name=key)
            role.permissions = roles[key][0]
            role.default = roles[key][1]
            db.session.add(role)
        db.session.commit()


# 分类
class Category(db.Model):
    __tablename__ = 'categorys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    posts = db.relationship('Post', backref='category', lazy='dynamic')  # 与post表关联

    @staticmethod
    def insert_categorys():
        categorylist = ["Android", "Flask", "Python", "CSS", "Html", "JavaScript", "杂文"]
        for category in categorylist:
            postcategory = Category.query.filter_by(name=category).first()
            if postcategory is None:#插入分类
                postcategory = Category(name=category)
                db.session.add(postcategory)
        db.session.commit()

    # def __repr__(self):
    #     return '<Category %r>' % self.name


# 博客表
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    body_html = db.Column(db.Text)
    # 外键author_id对应users.id
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    visits = db.Column(db.Integer, default=int(0))  # 访问数
    category_id = db.Column(db.Integer, db.ForeignKey('categorys.id'))

    # 获取热门博客前十篇
    @staticmethod
    def get_hot_post():
        posts = Post.query.all()
        if posts is not None and len(posts) > 0:
            posts_byvisits = sorted(posts, key=lambda s: s.visits, reverse=True)  # 降序排列
            if len(posts) > 10:
                length = 10
            else:
                length = len(posts)
            return posts_byvisits[0:length]

    # 生成模拟的虚拟博客数据100条
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            # offset表示从数据库的那个位置取值
            u = User.query.offset(randint(0, user_count - 1)).first()
            post = Post(title=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        timestamp=forgery_py.date.date(True), visits=0, author=u)
            db.session.add(post)
            db.session.commit()

    # on_change_body函数把body字段的文本渲染成html格式,结果保存在body_html中,自动高效的完成Markdown文本到html的转换
    # markdown函数是用来将markdown格式的文本转换成html格式，它接收两个参数，
    # 第一个参数是传进来的带转换格式的字符串，第二个参数是输出的格式，这里指定了html。
    # bleach的clean函数负责将多余的html标签进行清除，我们用allowed_tags制定了转换后允许存在的html标签，
    # 凡是不再这些指定标签内的其他标签，都会被清除。
    # bleach.linkify的作用是将html文本中的url转换成<a>标签，主要是因为markdown不支持自动将url转换成超链接
    @staticmethod
    def on_change_body(post, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
                        'pre',
                        'strong', 'ul', 'h1', 'h2', 'h3', 'p']
        post.body_html = bleach.linkify(
            bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True))

    # Post的json数据
    def to_json(self):
        json_post = {
            # external=True生成完整的 URL，
            'url': url_for('api.get_post', id=self.id, _external=True),  # 数据api地址
            'title': self.title,  # 标题
            'body': self.body,  # 内容
            'body_html': self.body_html,  # 内容html
            'timestamp': self.timestamp,  # 发布时间
            # 'author': url_for('api.get_user', id=self.author_id,
            #           _external=True),              #所属用户
            # 'comments': url_for('api.get_post_comments', id=self.id,
            #             _external=True),            #评论数据
            'comment_count': self.comments.count()  # 评论数
        }
        return json_post

    # 从json中获取body字段
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('博客内容不存在!')
        return Post(body=body)


# 数据库set事件的监听,只要posts表中的body字段更改了就会自动调用on_change_body函数
db.event.listen(Post.body, 'set', Post.on_change_body)


# 权限定义
class Permission:
    # 1.关注其他用户 	0b00000001(0x01)
    # 2.评论其他人的文章 	0b00000010(0x02)
    # 3.写文章 	0b00000100(0x04)
    # 4.管理他人的评论 	0b00001000(0x08)
    # 5.管理员 	0b10000000(0x80)

    # 权限或运算的结果就是Role的权限
    # 匿名 0b00000000（0x00） 未登录的用户。在程序中只有阅读权限
    # 用户 0b00000111（0x07） 具有发布文章、发表评论和关注其他用户的权限。这是新用户的默认角色(1|2|3)
    # 协管员 0b00001111（0x0f） 增加审查不当评论的权限(1|2|3|4)
    # 管理员 0b11111111（0xff） 具有所有权限，包括修改其他用户所属角色的权限(1|2|3|4|5)
    FOLLOW = 0x01  # 关注
    COMMENT = 0x02  # 评论
    WRITE_ARTICLES = 0x04  # 写文章
    MODERATE_COMMENTS = 0x08  # 管理他人发表的评论
    ADMINISTER = 0x80  # 管理员权限


# 定义一个AnonymousUser类,继承AnonymousUserMixin类
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 设置用户未登录时无权限,这样程序不用先检查用户是否登录就能自由调用can(),is_administrator()方法
login_manager.anonymous_user = AnonymousUser


# 加载用户login_manager的回调函数,如果能找到用户就返回该用户对象,否则返回None
@login_manager.user_loader
def load_user(user_id):
    print(int(user_id))
    return User.query.get(int(user_id))


# 评论表
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)
