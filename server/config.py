import os


def _load_env():
    """从同目录的 .env 文件加载配置（该文件不入库，部署时在服务器上创建）"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'photo-app-secret-key-2024'

    # MySQL 配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'photo_app')

    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4'
        % (MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # 火山引擎 TOS 对象存储
    TOS_ACCESS_KEY_ID = os.environ.get('TOS_ACCESS_KEY_ID', '')
    TOS_ACCESS_KEY_SECRET = os.environ.get('TOS_ACCESS_KEY_SECRET', '')
    TOS_REGION = os.environ.get('TOS_REGION', 'cn-beijing')
    TOS_ENDPOINT = os.environ.get('TOS_ENDPOINT', '')
    TOS_BUCKET = os.environ.get('TOS_BUCKET', '')

    # 豆包 Seedream API
    DOUBAO_API_KEY = os.environ.get('DOUBAO_API_KEY', '')
