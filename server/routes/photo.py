from flask import Blueprint, request, jsonify, send_from_directory
from models import Photo, Album, Background, Font, SystemSetting
from extensions import db
from routes.auth import token_required
from config import Config
from werkzeug.utils import secure_filename
import os
import uuid

photo_bp = Blueprint('photo', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@photo_bp.route('/upload', methods=['POST'])
@token_required
def upload_photo(current_user):
    """上传照片"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '文件名为空'})
    
    if not allowed_file(file.filename):
        return jsonify({'code': 400, 'message': '不支持的文件格式'})
    
    # 生成唯一文件名
    original_name = file.filename
    ext = original_name.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # 确保上传目录存在
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    
    # 创建数据库记录
    photo = Photo(
        filename=filename,
        original_name=original_name,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        user_id=current_user.id,
        album_id=request.form.get('album_id', type=int)
    )
    
    db.session.add(photo)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': photo.to_dict()
    })


@photo_bp.route('/list', methods=['GET'])
@token_required
def get_photos(current_user):
    """获取照片列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    album_id = request.args.get('album_id', type=int)
    
    query = Photo.query.filter_by(user_id=current_user.id, is_deleted=False)
    if album_id:
        query = query.filter_by(album_id=album_id)
    
    pagination = query.order_by(Photo.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'code': 200,
        'data': {
            'list': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@photo_bp.route('/<int:photo_id>', methods=['GET'])
@token_required
def get_photo(current_user, photo_id):
    """获取单张照片"""
    photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'code': 200,
        'data': photo.to_dict()
    })


@photo_bp.route('/<int:photo_id>', methods=['DELETE'])
@token_required
def delete_photo(current_user, photo_id):
    """删除照片（软删除）"""
    photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
    photo.is_deleted = True
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


@photo_bp.route('/file/<filename>', methods=['GET'])
def serve_photo(filename):
    """提供照片文件访问"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# 相册接口
@photo_bp.route('/albums', methods=['GET'])
@token_required
def get_albums(current_user):
    """获取相册列表"""
    albums = Album.query.filter_by(user_id=current_user.id).order_by(Album.created_at.desc()).all()
    return jsonify({
        'code': 200,
        'data': [a.to_dict() for a in albums]
    })


@photo_bp.route('/albums', methods=['POST'])
@token_required
def create_album(current_user):
    """创建相册"""
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'code': 400, 'message': '相册名称不能为空'})
    
    album = Album(
        name=name,
        description=data.get('description'),
        user_id=current_user.id
    )
    
    db.session.add(album)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': album.to_dict()
    })


@photo_bp.route('/albums/<int:album_id>', methods=['PUT'])
@token_required
def update_album(current_user, album_id):
    """更新相册"""
    album = Album.query.filter_by(id=album_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    if 'name' in data:
        album.name = data['name']
    if 'description' in data:
        album.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': album.to_dict()
    })


@photo_bp.route('/albums/<int:album_id>', methods=['DELETE'])
@token_required
def delete_album(current_user, album_id):
    """删除相册"""
    album = Album.query.filter_by(id=album_id, user_id=current_user.id).first_or_404()
    db.session.delete(album)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# 背景图接口（公开）
@photo_bp.route('/backgrounds', methods=['GET'])
def get_backgrounds():
    """获取背景图列表（供前端客户端使用）"""
    backgrounds = Background.query.filter_by(is_active=True).order_by(
        Background.created_at.desc()
    ).all()
    
    return jsonify({
        'code': 200,
        'data': [{
            'id': bg.id,
            'name': bg.name,
            'url': bg.to_dict()['url']  # 使用模型的 URL（支持 TOS）
        } for bg in backgrounds]
    })


# 字体接口（公开）
@photo_bp.route('/fonts', methods=['GET'])
def get_fonts():
    """获取字体列表（供前端客户端使用）"""
    fonts = Font.query.filter_by(is_active=True).order_by(
        Font.created_at.desc()
    ).all()
    
    return jsonify({
        'code': 200,
        'data': [{
            'id': f.id,
            'name': f.name,
            'url': f.to_dict()['url']  # 使用模型的 URL（支持 TOS）
        } for f in fonts]
    })


# Logo 接口（公开）
@photo_bp.route('/logo', methods=['GET'])
def get_logo():
    """获取品牌 Logo（供前端客户端使用）"""
    logo_url = SystemSetting.get('brand_logo')
    return jsonify({
        'code': 200,
        'data': {
            'url': logo_url
        }
    })


# 参考图接口（公开）
@photo_bp.route('/reference', methods=['GET'])
def get_reference():
    """获取合成参考图（供前端客户端使用）"""
    ref_url = SystemSetting.get('reference_image')
    return jsonify({
        'code': 200,
        'data': {
            'url': ref_url
        }
    })


# 提示词模式列表接口（公开）
@photo_bp.route('/prompts', methods=['GET'])
def get_prompts():
    """获取提示词模式列表（供前端客户端使用）"""
    import json
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
    
    return jsonify({
        'code': 200,
        'data': prompts
    })


# 文字描述设置接口（公开）
@photo_bp.route('/text-overlay', methods=['GET'])
def get_text_overlay():
    """获取文字描述设置（供前端客户端使用）"""
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
