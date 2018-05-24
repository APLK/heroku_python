from flask import jsonify, request, current_app, url_for

from app.api_1_0.decorators import permission_required
from app.modules import Permission, User, Post
from . import api

#根据id获取用户信息
@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())

#根据email删除用户信息
@api.route('/delete/user',methods=['POST'])
@permission_required(Permission.ADMINISTER)
def delete_user():
    #将json中的body字段解析出来,返回一个user对象
    user = User.from_json(request.json)
    #删除数据库
    if user is None:
        response = jsonify({'message': '邮箱地址不存在', 'code': 400})
        response.status_code = 400
    else:
        delete_user = user.deleteUser(user)
        if delete_user:
            response = jsonify({'message': '删除成功', 'code': 200})
            response.status_code = 200
        else:
            response = jsonify({'message': '删除失败', 'code': 400})
            response.status_code = 400
    return response

#根据用户id获取该用户所有的博客信息
@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

#获取用户好友所有的博客信息
@api.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', page=page-1,
                       _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', page=page+1,
                       _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
