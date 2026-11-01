from flask import Blueprint, request, jsonify, current_app
from models import User, Photo, Album, Background, CompositePhoto, Font, SystemSetting
from extensions import db
from routes.auth import admin_required
from config import Config
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats(current_user):
    """获取统计数据"""
    user_count = User.query.count()
    photo_count = CompositePhoto.query.filter_by(is_deleted=False).count()
    background_count = Background.query.filter_by(is_active=True).count()
    
    # 今日合成数量
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = CompositePhoto.query.filter(
        CompositePhoto.created_at >= today,
        CompositePhoto.is_deleted == False
    ).count()
    
    # 最新用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # 最新合成照片
    recent_photos = CompositePhoto.query.filter_by(is_deleted=False).order_by(
        CompositePhoto.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'code': 200,
        'data': {
            'user_count': user_count,
            'photo_count': photo_count,
            'background_count': background_count,
            'today_count': today_count,
            'recent_users': [{
                'id': u.id,
                'username': u.username,
                'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else None,
                'photo_count': CompositePhoto.query.filter_by(user_id=u.id, is_deleted=False).count(),
                'last_login': None
            } for u in recent_users],
            'recent_photos': [{
                'id': p.id,
                'url': p.file_path if p.file_path and p.file_path.startswith('http') else f'/uploads/composites/{p.filename}',
                'username': p.user.username if p.user else '未知',
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else None
            } for p in recent_photos]
        }
    })


@admin_bp.route('/stats/trend', methods=['GET'])
@admin_required
def get_trend(current_user):
    """获取趋势数据"""
    days = request.args.get('days', 7, type=int)
    
    dates = []
    counts = []
    
    for i in range(days - 1, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        count = CompositePhoto.query.filter(
            CompositePhoto.created_at >= start,
            CompositePhoto.created_at < end,
            CompositePhoto.is_deleted == False
        ).count()
        
        dates.append(start.strftime('%m-%d'))
        counts.append(count)
    
    return jsonify({
        'code': 200,
        'data': {
            'dates': dates,
            'counts': counts
        }
    })


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = User.query
    if keyword:
        query = query.filter(User.username.like(f'%{keyword}%'))
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user(current_user):
    """创建用户（后台管理员创建前端用户账号）"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    role = data.get('role', 'user')
    
    if not username:
        return jsonify({'code': 400, 'message': '用户名不能为空'})
    if not password:
        return jsonify({'code': 400, 'message': '密码不能为空'})
    if len(password) < 6:
        return jsonify({'code': 400, 'message': '密码长度至少6位'})
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'})
    
    # 检查邮箱是否已存在
    if email and User.query.filter_by(email=email).first():
        return jsonify({'code': 400, 'message': '邮箱已被使用'})
    
    # 创建用户
    user = User(username=username, email=email or None, role=role)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '用户创建成功',
        'data': user.to_dict()
    })


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(current_user, user_id):
    """获取单个用户"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'code': 200,
        'data': user.to_dict()
    })


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(current_user, user_id):
    """更新用户"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'email' in data:
        user.email = data['email']
    # AI 配额管理
    if 'ai_quota' in data:
        user.ai_quota = int(data['ai_quota'])
    if 'ai_used' in data:
        user.ai_used = int(data['ai_used'])
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


@admin_bp.route('/users/<int:user_id>/quota', methods=['PUT'])
@admin_required
def update_user_quota(current_user, user_id):
    """更新用户 AI 配额"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'ai_quota' in data:
        user.ai_quota = int(data['ai_quota'])
    if 'reset_used' in data and data['reset_used']:
        user.ai_used = 0
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'AI 配额更新成功',
        'data': {
            'user_id': user.id,
            'username': user.username,
            'ai_quota': user.ai_quota,
            'ai_used': user.ai_used,
            'ai_remaining': user.ai_remaining
        }
    })


@admin_bp.route('/users/quota/batch', methods=['PUT'])
@admin_required
def batch_update_quota(current_user):
    """批量更新用户 AI 配额"""
    data = request.get_json()
    
    default_quota = data.get('default_quota', 200)
    reset_all = data.get('reset_all', False)
    user_ids = data.get('user_ids', [])
    
    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
    else:
        users = User.query.filter(User.role != 'admin').all()
    
    for user in users:
        user.ai_quota = default_quota
        if reset_all:
            user.ai_used = 0
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': f'已更新 {len(users)} 个用户的配额',
        'data': {
            'updated_count': len(users),
            'new_quota': default_quota
        }
    })


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """删除用户"""
    if user_id == current_user.id:
        return jsonify({'code': 400, 'message': '不能删除自己'})
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


@admin_bp.route('/photos', methods=['GET'])
@admin_required
def get_photos(current_user):
    """获取照片列表（管理）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Photo.query.filter_by(is_deleted=False).order_by(
        Photo.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@admin_bp.route('/albums', methods=['GET'])
@admin_required
def get_albums(current_user):
    """获取相册列表（管理）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Album.query.order_by(Album.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


# ===================== 背景图管理 =====================

@admin_bp.route('/backgrounds', methods=['GET'])
@admin_required
def get_backgrounds(current_user):
    """获取背景图列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    pagination = Background.query.filter_by(is_active=True).order_by(
        Background.created_at.desc()
    ).paginate(page=page, per_page=page_size, error_out=False)
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [b.to_dict() for b in pagination.items],
            'total': pagination.total
        }
    })


@admin_bp.route('/backgrounds/upload', methods=['POST'])
@admin_required
def upload_background(current_user):
    """上传背景图（上传到 TOS）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '请选择文件'})
    
    # 检查文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'code': 400, 'message': '不支持的文件格式'})
    
    # 上传到 TOS
    file_data = file.read()
    file_size = len(file_data)
    filename = f"backgrounds/{uuid.uuid4().hex}.{ext}"
    tos_url = upload_to_tos_direct(file_data, filename)
    
    if not tos_url:
        return jsonify({'code': 500, 'message': '背景图上传到 TOS 失败，请检查 TOS 配置'})
    
    # 保存到数据库（存储 TOS URL）
    background = Background(
        name=secure_filename(file.filename),
        filename=tos_url,  # 存储完整 TOS URL
        file_path=tos_url,
        file_size=file_size
    )
    db.session.add(background)
    db.session.commit()
    
    # 返回结果，URL 直接是 TOS 公网地址
    result = background.to_dict()
    result['url'] = tos_url  # 覆盖为 TOS URL
    
    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': result
    })


@admin_bp.route('/backgrounds/<int:bg_id>', methods=['DELETE'])
@admin_required
def delete_background(current_user, bg_id):
    """删除背景图"""
    background = Background.query.get_or_404(bg_id)
    
    # TOS 上的文件不删除，只做软删除
    background.is_active = False
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ===================== 合成照片管理 =====================

@admin_bp.route('/photos', methods=['GET'])
@admin_required
def get_composite_photos(current_user):
    """获取合成照片列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    username = request.args.get('username', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = CompositePhoto.query.filter_by(is_deleted=False)
    
    if username:
        query = query.join(User).filter(User.username.like(f'%{username}%'))
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(CompositePhoto.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(CompositePhoto.created_at < end)
        except ValueError:
            pass
    
    pagination = query.order_by(CompositePhoto.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [p.to_dict() for p in pagination.items],
            'total': pagination.total
        }
    })


@admin_bp.route('/photos/<int:photo_id>', methods=['DELETE'])
@admin_required
def delete_composite_photo(current_user, photo_id):
    """删除合成照片"""
    photo = CompositePhoto.query.get_or_404(photo_id)
    
    # 软删除
    photo.is_deleted = True
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ===================== 字体管理 =====================

@admin_bp.route('/fonts', methods=['GET'])
@admin_required
def get_fonts(current_user):
    """获取字体列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    pagination = Font.query.order_by(
        Font.created_at.desc()
    ).paginate(page=page, per_page=page_size, error_out=False)
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [f.to_dict() for f in pagination.items],
            'total': pagination.total
        }
    })


@admin_bp.route('/fonts/upload', methods=['POST'])
@admin_required
def upload_font(current_user):
    """上传字体（上传到 TOS）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件'})
    
    # 验证文件类型
    allowed_extensions = ['ttf', 'otf', 'woff', 'woff2']
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'code': 400, 'message': f'不支持的字体格式，仅支持: {"、".join(allowed_extensions)}'})
    
    # 上传到 TOS
    file_data = file.read()
    file_size = len(file_data)
    filename = f"fonts/{uuid.uuid4().hex}.{ext}"
    tos_url = upload_to_tos_direct(file_data, filename)
    
    if not tos_url:
        return jsonify({'code': 500, 'message': '字体上传到 TOS 失败，请检查 TOS 配置'})
    
    # 获取字体名称
    original_name = secure_filename(file.filename)
    font_name = request.form.get('name') or original_name.rsplit('.', 1)[0]
    
    # 保存到数据库（存储 TOS URL）
    font = Font(
        name=font_name,
        filename=tos_url,  # 存储完整 TOS URL
        file_path=tos_url,
        file_size=file_size
    )
    db.session.add(font)
    db.session.commit()
    
    # 返回结果，URL 直接是 TOS 公网地址
    result = font.to_dict()
    result['url'] = tos_url  # 覆盖为 TOS URL
    
    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': result
    })


@admin_bp.route('/fonts/<int:font_id>', methods=['PUT'])
@admin_required
def update_font(current_user, font_id):
    """更新字体信息"""
    font = Font.query.get_or_404(font_id)
    data = request.get_json()
    
    if 'name' in data:
        font.name = data['name']
    if 'is_active' in data:
        font.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': font.to_dict()
    })


@admin_bp.route('/fonts/<int:font_id>', methods=['DELETE'])
@admin_required
def delete_font(current_user, font_id):
    """删除字体"""
    font = Font.query.get_or_404(font_id)
    
    # TOS 上的文件不删除，直接从数据库删除记录
    db.session.delete(font)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


@admin_bp.route('/fonts/<int:font_id>/toggle', methods=['POST'])
@admin_required
def toggle_font(current_user, font_id):
    """启用/禁用字体"""
    font = Font.query.get_or_404(font_id)
    font.is_active = not font.is_active
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '启用成功' if font.is_active else '禁用成功',
        'data': font.to_dict()
    })


# ========== Logo 管理 ==========

@admin_bp.route('/logo', methods=['GET'])
@admin_required
def get_logo(current_user):
    """获取当前 Logo"""
    logo_url = SystemSetting.get('brand_logo')
    return jsonify({
        'code': 200,
        'data': {
            'url': logo_url
        }
    })


@admin_bp.route('/logo/upload', methods=['POST'])
@admin_required
def upload_logo(current_user):
    """上传品牌 Logo（上传到 TOS）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件'})
    
    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'code': 400, 'message': '不支持的文件格式，仅支持 PNG/JPG/GIF/SVG/WEBP'})
    
    # 上传到 TOS
    file_data = file.read()
    filename = f'logo/brand_logo_{uuid.uuid4().hex[:8]}.{ext}'
    logo_url = upload_to_tos_direct(file_data, filename)
    
    if not logo_url:
        return jsonify({'code': 500, 'message': 'Logo 上传到 TOS 失败，请检查 TOS 配置'})
    
    # 更新系统设置
    SystemSetting.set('brand_logo', logo_url, '品牌 Logo')
    
    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': {
            'url': logo_url
        }
    })


@admin_bp.route('/logo', methods=['DELETE'])
@admin_required
def delete_logo(current_user):
    """删除品牌 Logo"""
    # TOS 上的文件不删除，只清除系统设置
    SystemSetting.set('brand_logo', None, '品牌 Logo')
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ========== 参考图管理 ==========

@admin_bp.route('/reference', methods=['GET'])
@admin_required
def get_reference(current_user):
    """获取当前参考图"""
    ref_url = SystemSetting.get('reference_image')
    return jsonify({
        'code': 200,
        'data': {
            'url': ref_url
        }
    })


@admin_bp.route('/reference/upload', methods=['POST'])
@admin_required
def upload_reference(current_user):
    """上传参考图（上传到 TOS）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件'})
    
    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'code': 400, 'message': '不支持的文件格式，仅支持 PNG/JPG/WEBP'})
    
    # 上传到 TOS
    file_data = file.read()
    filename = f'reference/reference_{uuid.uuid4().hex[:8]}.{ext}'
    ref_url = upload_to_tos_direct(file_data, filename)
    
    if not ref_url:
        return jsonify({'code': 500, 'message': '参考图上传到 TOS 失败，请检查 TOS 配置'})
    
    # 更新系统设置
    SystemSetting.set('reference_image', ref_url, '合成参考图')
    
    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': {
            'url': ref_url
        }
    })


@admin_bp.route('/reference', methods=['DELETE'])
@admin_required
def delete_reference(current_user):
    """删除参考图"""
    # TOS 上的文件不删除，只清除系统设置
    SystemSetting.set('reference_image', None, '合成参考图')
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ========== Doubao API 配置管理 ==========

@admin_bp.route('/mj-config', methods=['GET'])
@admin_required
def get_doubao_config(current_user):
    """获取 Doubao API 配置"""
    import json
    api_key = SystemSetting.get('doubao_api_key') or Config.DOUBAO_API_KEY
    model = SystemSetting.get('doubao_model') or 'doubao-seedream-4-5-251128'
    # 支持多提示词（JSON 格式）
    prompts_json = SystemSetting.get('doubao_prompts')
    if prompts_json:
        try:
            prompts = json.loads(prompts_json)
        except:
            prompts = [{'name': '模式1', 'content': prompts_json}]
    else:
        # 兼容旧的单提示词
        old_prompt = SystemSetting.get('doubao_prompt') or '将图1的人物与图2的背景完美融合，保持人物特征不变，自然融入背景场景'
        prompts = [{'name': '模式1', 'content': old_prompt}]
    size = SystemSetting.get('doubao_size') or '16:9'
    
    # API Key 只显示部分
    masked_key = api_key[:8] + '****' + api_key[-4:] if len(api_key) > 12 else '****' if api_key else ''
    
    # 支持的尺寸选项
    size_options = [
        {'value': '16:9', 'label': '16:9 横版 (2560x1440)', 'pixels': '2560x1440'},
        {'value': '9:16', 'label': '9:16 竖版 (1440x2560)', 'pixels': '1440x2560'},
        {'value': '1:1', 'label': '1:1 正方形 (2048x2048)', 'pixels': '2048x2048'},
        {'value': '4:3', 'label': '4:3 横版 (2304x1728)', 'pixels': '2304x1728'},
        {'value': '3:4', 'label': '3:4 竖版 (1728x2304)', 'pixels': '1728x2304'},
        {'value': '3:2', 'label': '3:2 横版 (2496x1664)', 'pixels': '2496x1664'},
        {'value': '2:3', 'label': '2:3 竖版 (1664x2496)', 'pixels': '1664x2496'},
        {'value': '21:9', 'label': '21:9 超宽 (3024x1296)', 'pixels': '3024x1296'},
        {'value': '2K', 'label': '2K 自动比例', 'pixels': '由模型判断'},
        {'value': '4K', 'label': '4K 自动比例', 'pixels': '由模型判断'},
    ]
    
    return jsonify({
        'code': 200,
        'data': {
            'apiKey': masked_key,
            'hasKey': bool(api_key),
            'model': model,
            'prompts': prompts,
            'size': size,
            'sizeOptions': size_options
        }
    })


@admin_bp.route('/mj-config', methods=['POST'])
@admin_required
def save_doubao_config(current_user):
    """保存 Doubao API 配置"""
    import json
    data = request.get_json()
    
    api_key = data.get('apiKey', '').strip()
    model = data.get('model', '').strip()
    prompts = data.get('prompts', [])  # 新的多提示词格式
    size = data.get('size', '').strip()
    
    # 只有非掩码的 Key 才保存
    if api_key and '****' not in api_key:
        SystemSetting.set('doubao_api_key', api_key, 'Doubao API Key')
    
    if model:
        SystemSetting.set('doubao_model', model, 'Doubao 模型')
    
    # 保存多提示词（JSON 格式）
    if prompts and len(prompts) > 0:
        SystemSetting.set('doubao_prompts', json.dumps(prompts, ensure_ascii=False), 'Doubao 提示词列表')
    
    if size:
        SystemSetting.set('doubao_size', size, 'Doubao 输出尺寸')
    
    return jsonify({
        'code': 200,
        'message': '保存成功'
    })


def upload_to_coze(image_data, filename='image.jpg'):
    """上传图片到 Coze 获取公网 URL"""
    import io
    
    # 获取 Coze API Key
    api_key = SystemSetting.get('coze_api_key')
    if not api_key:
        api_key = 'cztei_h4O5T40Hisbxq61uBO1DZWd0CIdLwzgcfJDxU9FKHJLnNXTlFYytqDUwnBHHpVP0q'
    
    url = 'https://api.coze.cn/v1/files/upload'
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    if isinstance(image_data, bytes):
        files = {'file': (filename, io.BytesIO(image_data), 'image/jpeg')}
    else:
        files = {'file': (filename, image_data, 'image/jpeg')}
    
    try:
        print(f"正在上传图片到 Coze: {filename}")
        response = requests.post(url, files=files, headers=headers, timeout=60)
        print(f"Coze 上传响应: {response.status_code}")
        result = response.json()
        print(f"Coze 上传结果: {result}")
        
        if result.get('code') == 0 and result.get('data'):
            # 返回文件 URL
            file_info = result['data']
            file_url = file_info.get('url') or file_info.get('file_url')
            if file_url:
                print(f"上传成功，URL: {file_url}")
                return file_url
            # 如果没有直接的 URL，可能需要用 file_id 构造
            file_id = file_info.get('id') or file_info.get('file_id')
            if file_id:
                # Coze 文件访问 URL 格式
                file_url = f"https://api.coze.cn/v1/files/{file_id}/content"
                print(f"构造文件 URL: {file_url}")
                return file_url
        else:
            print(f"Coze 上传失败: {result.get('msg') or result}")
    except Exception as e:
        print(f"Coze 上传异常: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def upload_image_to_hosting(image_data, filename='image.jpg'):
    """上传图片到图床获取公网 URL（尝试多个图床）"""
    import io
    import base64
    
    # 方案1: 使用 Coze 文件上传
    url = upload_to_coze(image_data, filename)
    if url:
        return url
    
    # 方案2: 使用 imgbb (需要 API Key)
    print("Coze 上传失败，尝试 imgbb...")
    try:
        if isinstance(image_data, bytes):
            b64_data = base64.b64encode(image_data).decode()
        else:
            b64_data = base64.b64encode(image_data.read()).decode()
        
        # imgbb 免费 API Key (可在 https://imgbb.com/api 获取)
        imgbb_key = '5e4f3d2c1b0a9f8e7d6c5b4a'  # 示例 key，需替换
        response = requests.post('https://api.imgbb.com/1/upload', data={
            'key': imgbb_key,
            'image': b64_data
        }, timeout=30)
        result = response.json()
        if result.get('success'):
            return result['data']['url']
    except Exception as e:
        print(f"imgbb 上传失败: {e}")
    
    # 方案3: 使用 catbox.moe (免费无需 API Key)
    print("imgbb 上传失败，尝试 catbox...")
    try:
        if isinstance(image_data, bytes):
            files = {'fileToUpload': (filename, io.BytesIO(image_data), 'image/jpeg')}
        else:
            files = {'fileToUpload': (filename, image_data, 'image/jpeg')}
        
        response = requests.post('https://catbox.moe/user/api.php', 
            data={'reqtype': 'fileupload'},
            files=files,
            timeout=60
        )
        if response.status_code == 200 and response.text.startswith('https://'):
            print(f"catbox 上传成功: {response.text}")
            return response.text.strip()
    except Exception as e:
        print(f"catbox 上传失败: {e}")
    
    return None


def upload_to_tos_direct(image_data, filename='image.jpg'):
    """直接上传图片到 TOS 获取公网 URL"""
    import tos
    import io
    import uuid
    from datetime import datetime
    from routes.tos import get_tos_config
    
    config = get_tos_config()
    
    if not config['access_key_id'] or not config['bucket']:
        print("TOS 未配置")
        return None
    
    try:
        # 创建 TOS 客户端
        client = tos.TosClientV2(
            ak=config['access_key_id'],
            sk=config['access_key_secret'],
            endpoint=config['endpoint'],
            region=config['region']
        )
        
        # 生成唯一的 key
        date_path = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8]
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'jpg'
        key = f"uploads/{date_path}/{unique_id}_{filename}"
        
        # 上传
        if isinstance(image_data, bytes):
            stream = io.BytesIO(image_data)
        else:
            stream = image_data
        
        result = client.put_object(config['bucket'], key, content=stream)
        print(f"TOS 上传成功: {result.request_id}")
        
        # 返回公网 URL
        url = f"https://{config['bucket']}.{config['endpoint']}/{key}"
        return url
        
    except Exception as e:
        print(f"TOS 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None


@admin_bp.route('/mj-config/test', methods=['POST'])
@admin_required
def test_doubao_composite(current_user):
    """测试 Doubao 图像合成（支持文件上传或 URL）"""
    from routes.ai import call_doubao_composite
    from routes.tos import generate_post_signature, get_tos_config
    
    photo_url = None
    background_url = None
    reference_url = None
    prompt = None
    
    # 检查是否是文件上传（multipart/form-data）
    if request.content_type and 'multipart/form-data' in request.content_type:
        # 处理用户照片上传
        if 'photo' in request.files:
            photo_file = request.files['photo']
            photo_data = photo_file.read()
            print(f"上传用户照片: {photo_file.filename}, 大小: {len(photo_data)} bytes")
            photo_url = upload_to_tos_direct(photo_data, photo_file.filename)
            if not photo_url:
                return jsonify({'code': 500, 'message': '用户照片上传失败，请检查 TOS 配置'})
            print(f"用户照片 URL: {photo_url}")
        
        # 处理背景图上传
        if 'background' in request.files:
            bg_file = request.files['background']
            bg_data = bg_file.read()
            print(f"上传背景图: {bg_file.filename}, 大小: {len(bg_data)} bytes")
            background_url = upload_to_tos_direct(bg_data, bg_file.filename)
            if not background_url:
                return jsonify({'code': 500, 'message': '背景图上传失败，请检查 TOS 配置'})
            print(f"背景图 URL: {background_url}")
        
        # 处理参考图上传（可选）
        if 'reference' in request.files:
            ref_file = request.files['reference']
            ref_data = ref_file.read()
            print(f"上传参考图: {ref_file.filename}, 大小: {len(ref_data)} bytes")
            reference_url = upload_to_tos_direct(ref_data, ref_file.filename)
            print(f"参考图 URL: {reference_url}")
        
        # 获取提示词
        prompt = request.form.get('prompt')
        
        # 也支持表单中传递 URL
        if not photo_url:
            photo_url = request.form.get('photoUrl')
        if not background_url:
            background_url = request.form.get('backgroundUrl')
        if not reference_url:
            reference_url = request.form.get('referenceUrl')
    else:
        # JSON 请求
        data = request.get_json() or {}
        photo_url = data.get('photoUrl')
        background_url = data.get('backgroundUrl')
        reference_url = data.get('referenceUrl')
        prompt = data.get('prompt')
    
    if not photo_url:
        return jsonify({'code': 400, 'message': '请上传用户照片或提供URL'})
    
    if not background_url:
        return jsonify({'code': 400, 'message': '请上传背景图或提供URL'})
    
    try:
        print(f"开始测试合成...")
        print(f"用户照片: {photo_url}")
        print(f"背景图: {background_url}")
        if reference_url:
            print(f"参考图: {reference_url}")
        if prompt:
            print(f"提示词: {prompt}")
        
        # 调用 Doubao 合成
        result_url = call_doubao_composite(photo_url, background_url, reference_url, prompt)
        
        return jsonify({
            'code': 200,
            'message': '合成成功',
            'data': {
                'resultUrl': result_url
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'测试失败: {str(e)}'})


# ========== TOS 对象存储配置管理 ==========

@admin_bp.route('/tos-config', methods=['GET'])
@admin_required
def get_tos_config(current_user):
    """获取 TOS 配置"""
    ak = SystemSetting.get('tos_access_key_id') or ''
    sk = SystemSetting.get('tos_access_key_secret') or ''
    region = SystemSetting.get('tos_region') or 'cn-beijing'
    endpoint = SystemSetting.get('tos_endpoint') or 'tos-cn-beijing.volces.com'
    bucket = SystemSetting.get('tos_bucket') or ''
    
    # 密钥只显示部分
    masked_ak = ak[:4] + '****' + ak[-4:] if len(ak) > 8 else '****' if ak else ''
    masked_sk = sk[:4] + '****' + sk[-4:] if len(sk) > 8 else '****' if sk else ''
    
    return jsonify({
        'code': 200,
        'data': {
            'accessKeyId': masked_ak,
            'accessKeySecret': masked_sk,
            'hasKey': bool(ak and sk),
            'region': region,
            'endpoint': endpoint,
            'bucket': bucket
        }
    })


@admin_bp.route('/tos-config', methods=['POST'])
@admin_required
def save_tos_config(current_user):
    """保存 TOS 配置"""
    data = request.get_json()
    
    ak = data.get('accessKeyId', '').strip()
    sk = data.get('accessKeySecret', '').strip()
    region = data.get('region', '').strip()
    endpoint = data.get('endpoint', '').strip()
    bucket = data.get('bucket', '').strip()
    
    # 只有非掩码的密钥才保存
    if ak and '****' not in ak:
        SystemSetting.set('tos_access_key_id', ak, 'TOS Access Key ID')
    
    if sk and '****' not in sk:
        SystemSetting.set('tos_access_key_secret', sk, 'TOS Access Key Secret')
    
    if region:
        SystemSetting.set('tos_region', region, 'TOS Region')
    
    if endpoint:
        SystemSetting.set('tos_endpoint', endpoint, 'TOS Endpoint')
    
    if bucket:
        SystemSetting.set('tos_bucket', bucket, 'TOS Bucket')
    
    return jsonify({
        'code': 200,
        'message': '保存成功'
    })


# ========== 文字描述设置管理（底部文字条） ==========

@admin_bp.route('/text-overlay', methods=['GET'])
@admin_required
def get_text_overlay_settings(current_user):
    """获取文字描述设置"""
    # 获取值，如果为空则使用默认值
    text_color = SystemSetting.get('text_overlay_text_color')
    bg_color = SystemSetting.get('text_overlay_bg_color')
    
    return jsonify({
        'code': 200,
        'data': {
            'enabled': SystemSetting.get('text_overlay_enabled', 'true') == 'true',
            'content': SystemSetting.get('text_overlay_content', ''),
            'fontId': int(SystemSetting.get('text_overlay_font_id', '0') or 0),
            'fontSize': int(SystemSetting.get('text_overlay_font_size', '24') or 24),
            'textColor': text_color if text_color else '#ffffff',
            'bgColor': bg_color if bg_color else 'rgba(0, 0, 0, 0.7)'
        }
    })


@admin_bp.route('/text-overlay', methods=['POST'])
@admin_required
def save_text_overlay_settings(current_user):
    """保存文字描述设置"""
    data = request.get_json()
    
    if 'enabled' in data:
        SystemSetting.set('text_overlay_enabled', 'true' if data['enabled'] else 'false', '文字描述-启用')
    if 'content' in data:
        SystemSetting.set('text_overlay_content', data['content'], '文字描述-内容')
    if 'fontId' in data:
        SystemSetting.set('text_overlay_font_id', str(data['fontId']), '文字描述-字体ID')
    if 'fontSize' in data:
        SystemSetting.set('text_overlay_font_size', str(data['fontSize']), '文字描述-字体大小')
    if 'textColor' in data:
        SystemSetting.set('text_overlay_text_color', data['textColor'], '文字描述-文字颜色')
    if 'bgColor' in data:
        SystemSetting.set('text_overlay_bg_color', data['bgColor'], '文字描述-背景颜色')
    
    return jsonify({
        'code': 200,
        'message': '保存成功'
    })
