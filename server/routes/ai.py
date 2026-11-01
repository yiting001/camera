from flask import Blueprint, request, jsonify, current_app
import base64
import os
import uuid
from datetime import datetime
import requests
import time
import json
from models import SystemSetting, User, CompositePhoto
from extensions import db
from flask import g
import tos
import jwt
from functools import wraps

ai_bp = Blueprint('ai', __name__)

# 存储目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
COMPOSITE_FOLDER = os.path.join(UPLOAD_FOLDER, 'composites')
BACKGROUND_FOLDER = os.path.join(UPLOAD_FOLDER, 'backgrounds')
TEMP_FOLDER = os.path.join(UPLOAD_FOLDER, 'temp')

# 确保目录存在
os.makedirs(COMPOSITE_FOLDER, exist_ok=True)
os.makedirs(BACKGROUND_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# JWT 密钥（与 auth.py 保持一致）
def get_current_user():
    """从请求头获取当前用户"""
    from config import Config
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        if user_id:
            return User.query.get(user_id)
    except:
        pass
    return None


def upload_local_to_tos(local_path):
    """
    将本地文件上传到 TOS 获取公网 URL
    """
    from routes.tos import get_tos_config
    
    config = get_tos_config()
    if not config['access_key_id'] or not config['bucket']:
        raise Exception('TOS 未配置')
    
    # 创建 TOS 客户端
    client = tos.TosClientV2(
        ak=config['access_key_id'],
        sk=config['access_key_secret'],
        endpoint=config['endpoint'],
        region=config['region']
    )
    
    # 生成 key
    ext = local_path.rsplit('.', 1)[-1] if '.' in local_path else 'jpg'
    date_path = datetime.now().strftime('%Y%m%d')
    unique_id = uuid.uuid4().hex[:8]
    key = f"backgrounds/{date_path}/{unique_id}.{ext}"
    
    # 上传文件
    with open(local_path, 'rb') as f:
        client.put_object(config['bucket'], key, content=f)
    
    # 返回公网 URL
    return f"https://{config['bucket']}.{config['endpoint']}/{key}"


def ensure_public_url(url):
    """
    确保 URL 是公网可访问的
    如果是本地 URL（localhost 或相对路径），则上传到 TOS
    """
    if not url:
        return url
    
    # 如果已经是公网 URL（非 localhost），直接返回
    if url.startswith('http') and 'localhost' not in url and '127.0.0.1' not in url:
        return url
    
    # 处理 localhost URL
    if 'localhost' in url or '127.0.0.1' in url:
        # 提取相对路径 /uploads/xxx -> uploads/xxx
        if '/uploads/' in url:
            relative_path = url.split('/uploads/')[-1]
            local_path = os.path.join(UPLOAD_FOLDER, relative_path)
        else:
            print(f"无法解析本地 URL: {url}")
            return url
    # 处理相对路径
    elif url.startswith('/uploads/'):
        local_path = os.path.join(UPLOAD_FOLDER, url.replace('/uploads/', ''))
    elif url.startswith('/'):
        # 其他相对路径
        local_path = os.path.join(os.path.dirname(UPLOAD_FOLDER), url.lstrip('/'))
    else:
        return url
    
    # 检查文件是否存在
    if not os.path.exists(local_path):
        print(f"本地文件不存在: {local_path}")
        return url
    
    try:
        print(f"上传本地文件到 TOS: {local_path}")
        public_url = upload_local_to_tos(local_path)
        print(f"上传成功: {public_url}")
        return public_url
    except Exception as e:
        print(f"上传到 TOS 失败: {e}")
        import traceback
        traceback.print_exc()
        return url



# Doubao 支持的图片尺寸
DOUBAO_SIZE_OPTIONS = {
    '16:9': '2560x1440',   # 默认
    '9:16': '1440x2560',   # 竖版
    '1:1': '2048x2048',    # 正方形
    '4:3': '2304x1728',
    '3:4': '1728x2304',
    '3:2': '2496x1664',
    '2:3': '1664x2496',
    '21:9': '3024x1296',   # 超宽
    '2K': '2K',            # 由模型判断
    '4K': '4K',            # 由模型判断
}

def get_doubao_config():
    """获取 Doubao API 配置"""
    api_key = SystemSetting.get('doubao_api_key')
    model = SystemSetting.get('doubao_model')
    size = SystemSetting.get('doubao_size')
    
    # 默认值（API Key 来自服务器上的 .env）
    if not api_key:
        from config import Config
        api_key = Config.DOUBAO_API_KEY
    if not model:
        model = 'doubao-seedream-4-5-251128'
    if not size:
        size = '16:9'  # 默认 16:9
    
    return api_key, model, size


def save_base64_image(base64_data, folder, prefix='img'):
    """保存base64图片到文件"""
    # 移除data URL前缀
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    # 解码并保存
    image_data = base64.b64decode(base64_data)
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.jpg"
    filepath = os.path.join(folder, filename)
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return filename, filepath, base64_data


def upload_to_temp_hosting(file_path):
    """
    上传图片到临时图床获取公网 URL
    使用 imgbb 免费图床（也可替换为其他服务）
    """
    # 方案1：使用本地服务器提供的 URL（需要公网可访问）
    # 方案2：使用 Coze 的文件上传 API
    # 这里我们直接返回本地路径，在调用时处理
    return None


def call_doubao_composite(photo_url, background_url, reference_url=None, prompt=None, size=None):
    """
    调用 Doubao Seedream API 进行图片合成
    
    参数:
    - photo_url: 用户照片的公网 URL (图1-人物)
    - background_url: 背景/服装图片的公网 URL (图2-参考)
    - reference_url: 额外参考图的公网 URL (可选)
    - prompt: 提示词 (可选，默认为换装提示)
    - size: 输出图片尺寸 (可选，默认为 16:9)
    
    返回:
    - 合成结果图片的 URL
    """
    api_key, model, default_size = get_doubao_config()
    
    if not api_key:
        raise Exception("Doubao API 未配置，请在管理后台配置 API Key")
    
    url = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 构建图片列表
    image_urls = [photo_url, background_url]
    if reference_url:
        image_urls.append(reference_url)
    
    # 默认提示词
    if not prompt:
        prompt = SystemSetting.get('doubao_prompt') or '将图1的人物与图2的背景完美融合，保持人物特征不变，自然融入背景场景'
    
    # 获取尺寸
    if not size:
        size = default_size
    # 将比例转换为像素值
    size_value = DOUBAO_SIZE_OPTIONS.get(size, size)
    
    payload = {
        'model': model,
        'prompt': prompt,
        'image': image_urls,
        'sequential_image_generation': 'disabled',
        'response_format': 'url',
        'size': size_value,
        'stream': False,
        'watermark': False
    }
    
    print(f"调用 Doubao API...")
    print(f"模型: {model}")
    print(f"尺寸: {size} -> {size_value}")
    print(f"图片1 (人物): {photo_url}")
    print(f"图片2 (背景): {background_url}")
    if reference_url:
        print(f"图片3 (参考): {reference_url}")
    print(f"提示词: {prompt}")
    
    # 发送请求
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    
    print(f"Doubao 响应状态: {response.status_code}")
    
    if response.status_code != 200:
        error_text = response.text
        print(f"Doubao API 错误: {error_text}")
        raise Exception(f"Doubao API 请求失败: {response.status_code} - {error_text}")
    
    result = response.json()
    print(f"Doubao 响应: {result}")
    
    # 解析结果
    if result.get('data') and len(result['data']) > 0:
        result_url = result['data'][0].get('url')
        if result_url:
            print(f"合成完成，结果: {result_url}")
            return result_url
    
    # 检查错误
    if result.get('error'):
        raise Exception(f"Doubao 合成失败: {result['error'].get('message', '未知错误')}")
    
    raise Exception("未获取到合成结果图片")


@ai_bp.route('/composite', methods=['POST'])
def generate_composite():
    """
    AI合成接口
    接收用户照片和背景，调用 Doubao API 生成合成图
    
    请求参数:
    - photo: 用户照片的公网URL (图1-人物)
    - background: 背景图片的公网URL (图2-背景)
    - reference: 参考图公网URL (可选)
    - prompt: 提示词 (可选)
    - size: 输出图片尺寸 (可选)
    
    返回:
    - compositeImage: 合成结果的URL
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        # 检查用户配额
        current_user = get_current_user()
        if current_user:
            if not current_user.can_generate_ai():
                return jsonify({
                    'code': 403, 
                    'message': '您的 AI 生成次数已用完，请联系管理员充值',
                    'data': {
                        'ai_quota': current_user.ai_quota,
                        'ai_used': current_user.ai_used,
                        'ai_remaining': 0
                    }
                }), 403
            print(f"用户 {current_user.username} 剩余次数: {current_user.ai_remaining}")
        
        photo_url = data.get('photo')
        background_url = data.get('background')
        reference_url = data.get('reference')
        prompt = data.get('prompt')
        size = data.get('size')
        
        if not photo_url:
            return jsonify({'code': 400, 'message': '缺少用户照片URL'}), 400
        
        if not background_url:
            return jsonify({'code': 400, 'message': '缺少背景图片URL'}), 400
        
        # 获取 Doubao API 配置
        api_key, model, default_size = get_doubao_config()
        if not api_key:
            return jsonify({'code': 500, 'message': 'Doubao API 未配置，请在管理后台配置'}), 500
        
        print(f"开始合成...")
        print(f"原始用户照片 URL: {photo_url}")
        print(f"原始背景 URL: {background_url}")
        
        # 确保所有 URL 都是公网可访问的
        photo_url = ensure_public_url(photo_url)
        background_url = ensure_public_url(background_url)
        if reference_url:
            reference_url = ensure_public_url(reference_url)
        
        print(f"公网用户照片: {photo_url}")
        print(f"公网背景: {background_url}")
        if reference_url:
            print(f"公网参考图: {reference_url}")
        if size:
            print(f"指定尺寸: {size}")
        
        # 调用 Doubao API 合成
        result_url = call_doubao_composite(photo_url, background_url, reference_url, prompt, size)
        
        if not result_url:
            return jsonify({'code': 500, 'message': 'AI合成失败，未获取到结果'}), 500
        
        # 合成成功，扣减用户配额
        if current_user:
            current_user.consume_ai_quota()
            print(f"用户 {current_user.username} 消耗1次配额，剩余: {current_user.ai_remaining}")
        
        return jsonify({
            'code': 200,
            'message': '合成成功',
            'data': {
                'compositeImage': result_url,
                'ai_remaining': current_user.ai_remaining if current_user else None
            }
        })
        
    except Exception as e:
        print(f"AI合成错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'合成失败: {str(e)}'}), 500


@ai_bp.route('/backgrounds', methods=['GET'])
def get_backgrounds():
    """获取预设背景列表"""
    backgrounds = [
        {'id': 'bg1', 'name': '海滩日落', 'url': '/backgrounds/beach.jpg'},
        {'id': 'bg2', 'name': '城市夜景', 'url': '/backgrounds/city.jpg'},
        {'id': 'bg3', 'name': '山林风光', 'url': '/backgrounds/forest.jpg'},
        {'id': 'bg4', 'name': '星空银河', 'url': '/backgrounds/galaxy.jpg'},
        {'id': 'bg5', 'name': '樱花盛开', 'url': '/backgrounds/sakura.jpg'},
        {'id': 'bg6', 'name': '欧式建筑', 'url': '/backgrounds/europe.jpg'},
    ]
    return jsonify({
        'code': 200,
        'data': backgrounds
    })


@ai_bp.route('/backgrounds/upload', methods=['POST'])
def upload_background():
    """上传自定义背景"""
    try:
        if 'background' not in request.files:
            return jsonify({'code': 400, 'message': '未找到背景文件'}), 400
        
        file = request.files['background']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '文件名为空'}), 400
        
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
        filename = f"custom_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{ext}"
        filepath = os.path.join(BACKGROUND_FOLDER, filename)
        
        file.save(filepath)
        
        return jsonify({
            'code': 200,
            'message': '上传成功',
            'data': {
                'id': f'custom_{uuid.uuid4().hex[:8]}',
                'name': file.filename,
                'url': f'/uploads/backgrounds/{filename}'
            }
        })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'上传失败: {str(e)}'}), 500


@ai_bp.route('/save-composite', methods=['POST'])
def save_composite():
    """
    保存合成图片到TOS对象存储并记录到数据库
    
    请求参数:
    - imageUrl: 合成图片的URL（Midjourney返回的URL）
    - imageData: 合成图片的base64数据（可选，如果没有URL）
    
    返回:
    - downloadUrl: TOS公网下载URL
    """
    try:
        data = request.get_json()
        
        image_url = data.get('imageUrl')
        image_data = data.get('imageData')
        
        if not image_url and not image_data:
            return jsonify({'code': 400, 'message': '缺少图片数据'}), 400
        
        # 生成保存文件名
        filename = f"composite_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.jpg"
        
        # 获取图片数据
        if image_url:
            # 从URL下载图片
            response = requests.get(image_url, timeout=60)
            if response.status_code != 200:
                return jsonify({'code': 500, 'message': '下载图片失败'}), 500
            image_bytes = response.content
        else:
            # 从base64解码
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        
        file_size = len(image_bytes)
        
        # 上传到TOS对象存储
        try:
            tos_url = upload_to_tos_direct(image_bytes, filename, 'composites')
        except Exception as e:
            print(f"上传TOS失败: {e}")
            # 如果TOS上传失败，回退到本地存储
            save_folder = os.path.join(UPLOAD_FOLDER, 'composites')
            os.makedirs(save_folder, exist_ok=True)
            filepath = os.path.join(save_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            tos_url = f'/uploads/composites/{filename}'
        
        # 保存到数据库
        composite = CompositePhoto(
            filename=filename,
            file_path=tos_url,
            file_size=file_size
        )
        db.session.add(composite)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '保存成功',
            'data': {
                'downloadUrl': tos_url,
                'filename': filename,
                'id': composite.id
            }
        })
        
    except Exception as e:
        print(f"保存图片错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'保存失败: {str(e)}'}), 500


def upload_to_tos_direct(file_data, filename, folder='composites'):
    """
    直接上传文件数据到TOS
    
    参数:
    - file_data: 文件二进制数据
    - filename: 文件名
    - folder: TOS中的文件夹
    
    返回:
    - 公网访问URL
    """
    # 获取TOS配置
    access_key_id = SystemSetting.get('tos_access_key_id')
    access_key_secret = SystemSetting.get('tos_access_key_secret')
    region = SystemSetting.get('tos_region', 'cn-beijing')
    endpoint = SystemSetting.get('tos_endpoint')
    bucket = SystemSetting.get('tos_bucket')
    
    if not all([access_key_id, access_key_secret, endpoint, bucket]):
        raise Exception('TOS配置不完整')
    
    # 创建TOS客户端
    client = tos.TosClientV2(
        ak=access_key_id,
        sk=access_key_secret,
        endpoint=endpoint,
        region=region
    )
    
    # 上传文件
    object_key = f"{folder}/{filename}"
    client.put_object(bucket, object_key, content=file_data)
    
    # 返回公网URL
    public_url = f"https://{bucket}.{endpoint.replace('https://', '').replace('http://', '')}/{object_key}"
    
    return public_url
