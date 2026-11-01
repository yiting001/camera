"""
火山引擎 TOS 对象存储相关路由
用于生成上传签名，供前端直传文件到 TOS
"""

from flask import Blueprint, request, jsonify
from config import Config
import tos
import time
import uuid
import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta

tos_bp = Blueprint('tos', __name__)

# TOS 配置默认值来自服务器上的 .env（不入库）
TOS_CONFIG = {
    'access_key_id': Config.TOS_ACCESS_KEY_ID,
    'access_key_secret': Config.TOS_ACCESS_KEY_SECRET,
    'region': Config.TOS_REGION,
    'endpoint': Config.TOS_ENDPOINT,
    'bucket': Config.TOS_BUCKET,
}


def get_tos_config():
    """从系统设置获取 TOS 配置"""
    from models import SystemSetting
    
    config = {
        'access_key_id': SystemSetting.get('tos_access_key_id') or TOS_CONFIG['access_key_id'],
        'access_key_secret': SystemSetting.get('tos_access_key_secret') or TOS_CONFIG['access_key_secret'],
        'region': SystemSetting.get('tos_region') or TOS_CONFIG['region'],
        'endpoint': SystemSetting.get('tos_endpoint') or TOS_CONFIG['endpoint'],
        'bucket': SystemSetting.get('tos_bucket') or TOS_CONFIG['bucket'],
        'sts_token': SystemSetting.get('tos_sts_token') or '',
    }
    return config


def generate_post_signature(bucket, key, config, expires=3600):
    """
    生成 TOS Post 上传签名
    参考: https://www.volcengine.com/docs/6349/1123288
    """
    ak = config['access_key_id']
    sk = config['access_key_secret']
    region = config['region']
    endpoint = config['endpoint']
    sts_token = config.get('sts_token', '')
    
    # 当前时间
    now = datetime.utcnow()
    date_str = now.strftime('%Y%m%dT%H%M%SZ')
    date_short = now.strftime('%Y%m%d')
    
    # 过期时间
    expiration = (now + timedelta(seconds=expires)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 凭证字符串
    credential = f"{ak}/{date_short}/{region}/tos/request"
    
    # 构建 Policy
    policy_dict = {
        "expiration": expiration,
        "conditions": [
            {"bucket": bucket},
            ["starts-with", "$key", key.rsplit('/', 1)[0] + '/' if '/' in key else ''],
            {"x-tos-algorithm": "TOS4-HMAC-SHA256"},
            {"x-tos-credential": credential},
            {"x-tos-date": date_str},
        ]
    }
    
    # 如果有 STS Token，添加到 policy
    if sts_token:
        policy_dict["conditions"].append({"x-tos-security-token": sts_token})
    
    # Base64 编码 Policy
    policy_json = json.dumps(policy_dict)
    policy_b64 = base64.b64encode(policy_json.encode()).decode()
    
    # 计算签名
    # 1. 派生签名密钥
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    k_date = sign(sk.encode('utf-8'), date_short)
    k_region = sign(k_date, region)
    k_service = sign(k_region, 'tos')
    k_signing = sign(k_service, 'request')
    
    # 2. 计算签名
    signature = hmac.new(k_signing, policy_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 构建返回数据
    result = {
        'key': key,
        'policy': policy_b64,
        'x-tos-algorithm': 'TOS4-HMAC-SHA256',
        'x-tos-credential': credential,
        'x-tos-date': date_str,
        'x-tos-signature': signature,
        'bucket': bucket,
        'endpoint': endpoint,
        'host': f"{bucket}.{endpoint}",
        'url': f"https://{bucket}.{endpoint}/{key}",
    }
    
    if sts_token:
        result['x-tos-security-token'] = sts_token
    
    return result


@tos_bp.route('/signature', methods=['GET'])
def get_upload_signature():
    """
    获取 TOS 上传签名
    参数:
    - key: 文件在 TOS 中的路径 (可选，不传则自动生成)
    - filename: 原始文件名
    - folder: 存储文件夹 (默认 uploads)
    """
    filename = request.args.get('filename', '')
    folder = request.args.get('folder', 'uploads')
    key = request.args.get('key', '')
    
    if not key:
        # 自动生成 key: folder/日期/uuid_filename
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'jpg'
        date_path = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8]
        key = f"{folder}/{date_path}/{unique_id}_{filename}" if filename else f"{folder}/{date_path}/{unique_id}.{ext}"
    
    config = get_tos_config()
    
    if not config['access_key_id'] or not config['access_key_secret'] or not config['bucket']:
        return jsonify({
            'code': 500,
            'message': 'TOS 未配置，请在管理后台配置 TOS 参数'
        }), 500
    
    try:
        result = generate_post_signature(config['bucket'], key, config)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        print(f"生成 TOS 签名失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'生成签名失败: {str(e)}'
        }), 500


@tos_bp.route('/config', methods=['GET'])
def get_tos_client_config():
    """获取 TOS 客户端配置（不包含密钥）"""
    config = get_tos_config()
    return jsonify({
        'code': 200,
        'data': {
            'bucket': config['bucket'],
            'endpoint': config['endpoint'],
            'region': config['region'],
            'configured': bool(config['access_key_id'] and config['bucket'])
        }
    })
