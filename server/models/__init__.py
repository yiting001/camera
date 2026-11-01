from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(20), default='user')  # admin, user
    avatar = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    ai_quota = db.Column(db.Integer, default=200)  # AI生成总次数配额
    ai_used = db.Column(db.Integer, default=0)     # AI生成已使用次数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def ai_remaining(self):
        """剩余AI生成次数"""
        return max(0, (self.ai_quota or 200) - (self.ai_used or 0))
    
    def can_generate_ai(self):
        """检查是否还有AI生成次数"""
        # 管理员不限制
        if self.role == 'admin':
            return True
        return self.ai_remaining > 0
    
    def consume_ai_quota(self):
        """消耗一次AI生成次数"""
        if self.role != 'admin':
            self.ai_used = (self.ai_used or 0) + 1
            db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'avatar': self.avatar,
            'is_active': self.is_active,
            'ai_quota': self.ai_quota or 200,
            'ai_used': self.ai_used or 0,
            'ai_remaining': self.ai_remaining,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Photo(db.Model):
    """照片表"""
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256))
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(50))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    description = db.Column(db.Text)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    album = db.relationship('Album', backref=db.backref('photos', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('photos', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'description': self.description,
            'album_id': self.album_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Album(db.Model):
    """相册表"""
    __tablename__ = 'albums'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cover_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('albums', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover_id': self.cover_id,
            'is_public': self.is_public,
            'photo_count': self.photos.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Background(db.Model):
    """背景图表"""
    __tablename__ = 'backgrounds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    filename = db.Column(db.String(512), nullable=False)  # 可能存储TOS URL
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # 如果 filename 是完整 URL（TOS），直接使用；否则拼接本地路径
        url = self.filename if self.filename.startswith('http') else f'/uploads/backgrounds/{self.filename}'
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'url': url,
            'file_size': self.file_size,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Font(db.Model):
    """字体表"""
    __tablename__ = 'fonts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    filename = db.Column(db.String(512), nullable=False)  # 可能存储TOS URL
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # 如果 filename 是完整 URL（TOS），直接使用；否则拼接本地路径
        url = self.filename if self.filename.startswith('http') else f'/uploads/fonts/{self.filename}'
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'url': url,
            'file_size': self.file_size,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CompositePhoto(db.Model):
    """合成照片表"""
    __tablename__ = 'composite_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)
    background_id = db.Column(db.Integer, db.ForeignKey('backgrounds.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    background = db.relationship('Background', backref=db.backref('composites', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('composites', lazy='dynamic'))
    
    def to_dict(self):
        # 如果 file_path 是完整 URL（TOS），直接使用；否则拼接本地路径
        url = self.file_path if self.file_path.startswith('http') else f'/uploads/composites/{self.filename}'
        return {
            'id': self.id,
            'filename': self.filename,
            'url': url,
            'file_size': self.file_size,
            'background_id': self.background_id,
            'background_name': self.background.name if self.background else None,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemSetting(db.Model):
    """系统设置表"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(256))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set(cls, key, value, description=None):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
