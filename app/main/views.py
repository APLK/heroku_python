# encoding:utf-8
'''
@author:lk

@time:2017/9/5 

@desc:页面布局

'''
from flask import render_template, redirect, url_for, abort, flash, request, current_app, \
    make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries

from app import db
from app.decorators import admin_required, permission_required
from app.modules import User, Permission, Post, Role, Comment, Category
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm


# 请求之后检查数据库查询的时间
@main.after_app_request
def after_request(response):
    # get_debug_queries() 函数返回一个列表，其元素是请求中执行的查询
    # parameters SQL 语句使用的参数
    # start_time 执行查询时的时间
    # end_time 返回查询结果时的时间
    # duration 查询持续的时间，单位为秒
    # context 表示查询在源码中所处位置的字符串
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


# Selenium测试时测试完毕了需要关闭后台中的服务器
@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return '正在关闭服务器...'


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()  # 定义一个文本字段和一个提交按钮
    # 如果有发表的权限
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        # 将Post对象通过User中的backref的author字段建立关联,表示该博客所属于当前用户发表的
        post = Post(title=form.title.data, body=form.body.data,
                    author=current_user._get_current_object(),
                    category=Category.query.get(form.category.data))
        db.session.add(post)
        # 重定向到index,.号代表命名空间,可以在不同的蓝本中使用相同的端点,是main.index的省略写法
        # 命名空间是当前请求所在的蓝本
        # 定义视图函数,而不产生冲突
        return redirect(url_for('.index'))
    # 渲染的页数从请求的查询字符串request.args中获取,如果没有明确指定页码从第一页开始
    # request.args要操作 URL （如 ?key=value ）中提交的参数可以使用 args 属性
    # type保证参数无法转化为整数时返回默认值
    page = request.args.get('page', 1, type=int)

    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    hot_post = Post.get_hot_post()  # 取出post表中的热门博客
    categorys = Category.query.all()  # 取出category表中的分类
    # paginate方法中的第一个参数page是必须参数,per_page表示每页显示数量,
    # error_out=True表示如果请求的页数超过范围返回404,否则返回空列表
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items  # 每页的博客数据
    return render_template('index.html', form=form, posts=posts, categorys=categorys,
                           show_followed=show_followed, pagination=pagination, isshow=True,
                           hot_posts=hot_post)
    # return render_template('index.html', form=form,
    #                        name=session.get('name'),
    #                        known=session.get('known', False),
    #                        current_time=datetime.utcnow)


# 查看所有文章
@main.route('/all')
@login_required
def show_all():
    # 因为cookie只能在响应对象中设置,所以要使用make_response()方法来创建响应体
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)  # max_age是cookies的最大有效期
    return resp


# 查看所关注用户的文章
@main.route('/followed')
@login_required
def show_followed():
    # 因为cookie只能在响应对象中设置,所以要使用make_response()方法来创建响应体
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)  # max_age是cookies的最大有效期
    return resp


# 查看分类文章
@main.route('/category/<name>')
@login_required
def show_category(name):
    id = request.args.get('id')
    print(id)
    form = PostForm()  # 定义一个文本字段和一个提交按钮
    # 如果有发表的权限
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        # 将Post对象通过User中的backref的author字段建立关联,表示该博客所属于当前用户发表的
        post = Post(title=form.title.data, body=form.body.data,
                    author=current_user._get_current_object(),
                    category=Category.query.get(form.category.data))
        db.session.add(post)
        # 重定向到index,.号代表命名空间,可以在不同的蓝本中使用相同的端点,是main.index的省略写法
        # 命名空间是当前请求所在的蓝本
        # 定义视图函数,而不产生冲突
        return redirect(url_for('.index'))
    # 渲染的页数从请求的查询字符串request.args中获取,如果没有明确指定页码从第一页开始
    # request.args要操作 URL （如 ?key=value ）中提交的参数可以使用 args 属性
    # type保证参数无法转化为整数时返回默认值
    page = request.args.get('page', 1, type=int)

    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_category_posts(id)
    else:
        query = Post.query.filter_by(category_id=id)
    hot_post = Post.get_hot_post()  # 取出post表中的热门博客
    categorys = Category.query.all()  # 取出category表中的分类
    # paginate方法中的第一个参数page是必须参数,per_page表示每页显示数量,
    # error_out=True表示如果请求的页数超过范围返回404,否则返回空列表
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items  # 每页的博客数据
    return render_template('index.html', form=form, posts=posts, categorys=categorys,
                           show_followed=show_followed, pagination=pagination, isshow=True,
                           hot_posts=hot_post)


# 个人博客主页
@main.route('/user/<username>')
@login_required
def user(username):
    # if username != current_user.username:
    #     abort(403)
    # 根据用户名查询User对象
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    # 按博客发表时间排序,只显示该用户发表的博客数据
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


# 分享博客链接
@main.route('/edit-profile', methods=['GET'])
def share():
    pass

# 编辑个人资料
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    # 如果表单被提交了就更新数据库数据
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('个人资料已经更新了')
        return redirect(url_for('.user', username=current_user.username))
    # 取出current_user的资料数据渲染页面
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


# 管理员博客编辑
# 自定义的管理员装饰器admin_required
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    # if id != current_user.id:
    #     abort(403)
    user = User.query.get_or_404(id)  # Flask_SqkAlchemy提供的get_or_404函数,如果提供的id未找到就404
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('个人资料已经更新了')
        return redirect(url_for('.user', username=current_user.username))
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.confirmed.data = current_user.confirmed
    form.role.data = current_user.role
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, user=user)


# 编辑博客
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    # if id != current_user.id:
    #     abort(403)
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.MODERATE_COMMENTS):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('博客已经被重新编辑了')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


# 添加关注
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    # if username != current_user.username:
    #     abort(403)
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    # 如果该用户被我关注过了
    if current_user.is_following(user):
        flash('您已经关注过该用户了!')
        return redirect(url_for('.user', username=username))
    # 否则就去添加我关注该用户
    current_user.follow(user)
    flash('您刚刚关注了%s用户' % username)
    return redirect(url_for('.user', username=username))


# 取消关注
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    # 如果该用户还未被我关注过了
    if not current_user.is_following(user):
        flash('您还未关注该用户哦!')
        return redirect(url_for('.user', username=username))
    # 否则取消关注该用户
    current_user.unfollow(user)
    flash('您刚刚已经取消关注%s了' % username)
    return redirect(url_for('.user', username=username))


# 粉丝列表
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    # 将该user用户关联表中的followers(主动关注者)数据分页(follower_id为user.id的)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    # 从每页中遍历取出该用户所有粉丝的user对象,注意此处是item.follower
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="粉丝",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


# 关注列表
@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    # 将该user主动关注的所有用户列表数据分页
    # user.followed取的是follower_id的列表
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    # 根据follower_id的值查找follows表中的followed_id的值,所以用itm.followed表示
    # 从每页中遍历取出该用户所有关注的user对象,注意此处是item.followed
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="关注",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


# 博客新增和评论博客
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    post.visits += 1  # 访问数+1
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('评论成功!')
        # 在 url_for() 函数的参数中把 page 设为 -1，这是个特殊的页
        # 数，用来请求评论的最后一页，所以刚提交的评论才会出现在页面中。
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
               current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


# 评论列表
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


# 更改评论的不可见,只有拥有MODERATE_COMMENTS权限的才能操作
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    # if id != current_user.id:
    #     abort(403)
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


# 更改评论的可见,只有拥有MODERATE_COMMENTS权限的才能操作
@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    # if id != current_user.id:
    #     abort(403)
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


# 搜索博客
@main.route('/search', methods=['POST'])
def search():
    form = request.form
    print(form['search'])
    if request.method == "POST" and len(form['search']) > 0:
        return redirect(url_for('.search_results', query=form['search']))
    return redirect(url_for('.index'))


# 搜索博客结果
@main.route('/search_results/<query>')
def search_results(query):
    print(query)
    posts = Post.query.filter(Post.body.like('%' + query + '%')).all()
    print(len(posts))
    return render_template('search_results.html', query=query, posts=posts)
