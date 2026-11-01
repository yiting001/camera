# -*- coding: utf-8 -*-
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db, migrate
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/uploads/*": {"origins": "*"}
    }, supports_credentials=True)
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.photo import photo_bp
    from routes.ai import ai_bp
    from routes.tos import tos_bp
    from routes.share import share_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(photo_bp, url_prefix='/api/photo')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(tos_bp, url_prefix='/api/tos')
    app.register_blueprint(share_bp)
    
    # 静态文件服务 - 上传的图片
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filename)
    
    # 创建上传目录
    os.makedirs(os.path.join(app.root_path, 'uploads', 'backgrounds'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'uploads', 'composites'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'uploads', 'fonts'), exist_ok=True)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
