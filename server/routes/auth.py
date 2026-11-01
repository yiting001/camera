from flask import Blueprint, request, jsonify
from models import User
from extensions import db
import jwt
from datetime import datetime, timedelta
from functools import wraps
from config import Config

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """JWT 验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'code': 401, 'message': '缺少认证令牌'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user or not current_user.is_active:
                return jsonify({'code': 401, 'message': '用户不存在或已禁用'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': '令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': '无效的令牌'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin_login = data.get('admin', False)  # 是否为管理后台登录
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'})
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误'})
    
    if not user.is_active:
        return jsonify({'code': 403, 'message': '账户已被禁用'})
    
    # 管理后台登录需要验证管理员权限
    if is_admin_login and user.role != 'admin':
        return jsonify({'code': 403, 'message': '您没有管理员权限，无法登录管理后台'})
    
    # 生成 JWT
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, Config.SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'})
    
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'})
    
    if email and User.query.filter_by(email=email).first():
        return jsonify({'code': 400, 'message': '邮箱已被注册'})
    
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '注册成功',
        'data': user.to_dict()
    })


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户信息"""
    return jsonify({
        'code': 200,
        'data': current_user.to_dict()
    })


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用户信息"""
    data = request.get_json()
    
    if 'email' in data:
        current_user.email = data['email']
    if 'avatar' in data:
        current_user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': current_user.to_dict()
    })
