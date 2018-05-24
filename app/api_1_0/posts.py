# encoding:utf-8
'''
@author:lk

@time:2017/9/22

@desc:api的博客接口

'''
from flask import jsonify, request, g, url_for, current_app

from app.api_1_0.decorators import permission_required
from app.modules import Post, Permission
from .. import db
from . import api
from .errors import forbidden

#获取所有博客信息
@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

#根据id获取博客信息
@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())

# 新增博客
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    #将json中的body字段解析出来,返回一个post对象
    post = Post.from_json(request.json)
    post.author = g.current_user
    print(g.current_user)
    #加入数据库
    db.session.add(post)
    db.session.commit()
    # 201请求成功完成并创建了一个新资源
    print('new_post000')
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id, _external=True)}

#编辑博客信息
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMINISTER):
        return forbidden('权限不够!')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())
