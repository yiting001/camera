# -*- coding: utf-8 -*-
"""
图片分享下载路由
二维码不再指向对象存储(TOS/OSS)直链，而是指向本服务器 /s/<id> 分享页：
- 分享页将图片以 base64 内嵌，微信内置浏览器可直接打开，长按即可保存
- /s/<id>/raw 返回原始图片流（Content-Type/内联头正确），作为兜底直链
"""
from flask import Blueprint, request, jsonify, Response
from extensions import db
from models import CompositePhoto
import base64
import os
import uuid

share_bp = Blueprint('share', __name__)

SHARE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'shares')
os.makedirs(SHARE_FOLDER, exist_ok=True)


def _detect_ext(data):
    """根据文件头判断图片格式"""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    return 'jpg'


def _find_share_file(share_id):
    """按 id 查找分享图片文件，id 只允许字母数字，防目录穿越"""
    if not share_id or not share_id.isalnum():
        return None
    for ext in ('jpg', 'jpeg', 'png'):
        path = os.path.join(SHARE_FOLDER, '%s.%s' % (share_id, ext))
        if os.path.exists(path):
            return path
    return None


@share_bp.route('/api/photo/share', methods=['POST'])
def create_share():
    """保存图片并生成站内分享短链接

    请求参数(JSON):
    - imageData: 图片的 base64 数据（可带 data:image/...;base64, 前缀）
    - imageUrl:  图片的公网 URL（可选，与 imageData 二选一）

    返回:
    - sharePath: /s/<id> 分享页路径，客户端拼接服务器地址后生成二维码
    """
    data = request.get_json(silent=True) or {}
    image_data = data.get('imageData')
    image_url = data.get('imageUrl')

    image_bytes = None
    if image_data:
        b64 = image_data.split(',', 1)[1] if ',' in image_data else image_data
        try:
            image_bytes = base64.b64decode(b64)
        except Exception:
            return jsonify({'code': 400, 'message': '图片数据无效'})
    elif image_url:
        import requests
        try:
            resp = requests.get(image_url, timeout=60)
            resp.raise_for_status()
            image_bytes = resp.content
        except Exception:
            return jsonify({'code': 500, 'message': '下载图片失败'})

    if not image_bytes:
        return jsonify({'code': 400, 'message': '缺少图片数据'})

    share_id = uuid.uuid4().hex[:12]
    filename = '%s.%s' % (share_id, _detect_ext(image_bytes))
    with open(os.path.join(SHARE_FOLDER, filename), 'wb') as f:
        f.write(image_bytes)

    composite = CompositePhoto(
        filename=filename,
        file_path='/s/%s' % share_id,
        file_size=len(image_bytes)
    )
    db.session.add(composite)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '保存成功',
        'data': {
            'shareId': share_id,
            'sharePath': '/s/%s' % share_id,
            'filename': filename,
            'id': composite.id
        }
    })


@share_bp.route('/s/<share_id>', methods=['GET'])
def share_page(share_id):
    """分享落地页：图片以 base64 内嵌，微信内长按图片即可保存"""
    path = _find_share_file(share_id)
    if not path:
        return ('<meta charset="utf-8"><h3 style="text-align:center;margin-top:80px;">图片不存在或已过期</h3>', 404)

    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    mime = 'image/png' if path.endswith('.png') else 'image/jpeg'

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>照片下载</title>
<style>
  body {{ margin:0; background:#111; font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif; }}
  .wrap {{ max-width:640px; margin:0 auto; padding:16px; text-align:center; }}
  img.photo {{ width:100%; height:auto; display:block; border-radius:8px; }}
  .btn {{ display:block; margin:16px auto 8px; padding:14px 0; background:#409eff; color:#fff;
         font-size:17px; border-radius:8px; text-decoration:none; }}
  .btn2 {{ display:block; margin:0 auto; padding:10px 0; color:#8ab4f8; font-size:14px; text-decoration:none; }}
  .tip {{ color:#aaa; font-size:14px; margin:12px 0 4px; }}
</style>
</head>
<body>
<div class="wrap">
  <p class="tip">长按下方图片可保存到手机相册</p>
  <img class="photo" alt="照片" src="data:{mime};base64,{b64}">
  <a class="btn" href="data:{mime};base64,{b64}" download="photo.jpg">保存图片</a>
  <a class="btn2" href="/s/{share_id}/raw" target="_blank">打不开？点此查看原图</a>
</div>
</body>
</html>""".format(b64=b64, mime=mime, share_id=share_id)
    return Response(html, mimetype='text/html')


@share_bp.route('/s/<share_id>/raw', methods=['GET'])
def share_raw(share_id):
    """原始图片流：Content-Type 正确 + 内联展示，浏览器/微信可直接显示并长按保存"""
    path = _find_share_file(share_id)
    if not path:
        return jsonify({'code': 404, 'message': '图片不存在'}), 404

    ext = path.rsplit('.', 1)[-1].lower()
    mime = 'image/png' if ext == 'png' else 'image/jpeg'
    with open(path, 'rb') as f:
        data = f.read()

    resp = Response(data, mimetype=mime)
    resp.headers['Content-Disposition'] = 'inline; filename="%s.%s"' % (share_id, ext)
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp
