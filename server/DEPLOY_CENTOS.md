# CentOS 服务器部署文档

## 环境要求

- CentOS 7.x
- Python 3.6.8
- MySQL 5.7+ 或 MariaDB 10.x
- Nginx（可选，用于反向代理）

---

## 一、安装基础环境

### 1.1 安装 Python 3.6（如未安装）

```bash
# 安装依赖
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel

# CentOS 7 默认源有 Python 3.6
sudo yum install -y python3 python3-pip python3-devel
```

### 1.2 安装 MySQL/MariaDB

```bash
# 安装 MariaDB
sudo yum install -y mariadb-server mariadb-devel

# 启动并设置开机自启
sudo systemctl start mariadb
sudo systemctl enable mariadb

# 初始化安全设置
sudo mysql_secure_installation
```

### 1.3 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 执行以下 SQL
CREATE DATABASE photo_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'photo_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON photo_app.* TO 'photo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 二、部署后端应用

### 2.1 上传代码

将 `server` 目录上传到服务器，例如 `/opt/photo-app/`

```bash
# 创建目录
sudo mkdir -p /opt/photo-app
sudo chown $(whoami):$(whoami) /opt/photo-app

# 使用 scp 上传（在本地执行）
scp -r ./server/* user@your_server_ip:/opt/photo-app/
```

### 2.2 创建 Python 虚拟环境

```bash
cd /opt/photo-app

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖（使用 Python 3.6 兼容版本）
pip install -r requirements-py36.txt
```

### 2.3 配置应用

凭据不再写在代码里，改为读取同目录的 `.env` 文件（已被 `.gitignore` 排除）：

```bash
cd /opt/photo-app
cp .env.example .env
chmod 600 .env
vi .env   # 填入 MySQL、TOS、豆包 API 的真实值
```

`.env` 支持的配置项见 `.env.example`；也可以不用文件，直接 `export` 同名环境变量。

如果确实想改代码里的默认值，编辑 `config.py`（其中的配置项都通过 `os.environ.get` 读取）。

### 2.4 初始化数据库

```bash
# 确保虚拟环境已激活
source /opt/photo-app/venv/bin/activate

cd /opt/photo-app

# 运行初始化脚本
python init_db.py
```

如果没有 `init_db.py`，可以通过 Flask shell 初始化：

```bash
export FLASK_APP=app.py
flask shell

# 在 shell 中执行
>>> from extensions import db
>>> db.create_all()
>>> exit()
```

### 2.5 创建上传目录

```bash
mkdir -p /opt/photo-app/uploads/{backgrounds,composites,fonts,temp}
chmod -R 755 /opt/photo-app/uploads
```

---

## 三、使用 Gunicorn 运行

### 3.1 创建 Gunicorn 配置

```bash
cat > /opt/photo-app/gunicorn.conf.py << 'EOF'
# Gunicorn 配置文件
bind = '0.0.0.0:5001'
workers = 4
threads = 2
worker_class = 'sync'
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = '/opt/photo-app/logs/access.log'
errorlog = '/opt/photo-app/logs/error.log'
loglevel = 'info'
daemon = False
EOF

# 创建日志目录
mkdir -p /opt/photo-app/logs
```

### 3.2 创建 WSGI 入口文件

```bash
cat > /opt/photo-app/wsgi.py << 'EOF'
from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
EOF
```

### 3.3 测试运行

```bash
cd /opt/photo-app
source venv/bin/activate

# 测试运行
gunicorn -c gunicorn.conf.py wsgi:application
```

访问 `http://your_server_ip:5001/api/auth/login` 测试是否正常。

---

## 四、配置 Systemd 服务（开机自启）

### 4.1 创建服务文件

```bash
sudo cat > /etc/systemd/system/photo-app.service << 'EOF'
[Unit]
Description=Photo App Backend Service
After=network.target mariadb.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/photo-app
Environment="PATH=/opt/photo-app/venv/bin"
ExecStart=/opt/photo-app/venv/bin/gunicorn -c gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 4.2 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start photo-app

# 设置开机自启
sudo systemctl enable photo-app

# 查看状态
sudo systemctl status photo-app

# 查看日志
sudo journalctl -u photo-app -f
```

---

## 五、配置 Nginx 反向代理（可选）

### 5.1 安装 Nginx

```bash
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 5.2 配置 Nginx

```bash
sudo cat > /etc/nginx/conf.d/photo-app.conf << 'EOF'
server {
    listen 80;
    server_name your_domain.com;  # 替换为你的域名或 IP

    # 上传文件大小限制
    client_max_body_size 20M;

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # 静态文件（上传的图片）
    location /uploads/ {
        alias /opt/photo-app/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx
```

### 5.3 配置防火墙

```bash
# 开放端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

---

## 六、常用运维命令

```bash
# 查看服务状态
sudo systemctl status photo-app

# 重启服务
sudo systemctl restart photo-app

# 停止服务
sudo systemctl stop photo-app

# 查看实时日志
tail -f /opt/photo-app/logs/error.log
tail -f /opt/photo-app/logs/access.log

# 进入虚拟环境
source /opt/photo-app/venv/bin/activate

# 手动运行（调试用）
cd /opt/photo-app
source venv/bin/activate
python app.py
```

---

## 七、更新部署

```bash
# 1. 上传新代码
scp -r ./server/* user@server:/opt/photo-app/

# 2. 重启服务
sudo systemctl restart photo-app
```

---

## 八、故障排查

### 8.1 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u photo-app -n 50 --no-pager

# 手动测试运行
cd /opt/photo-app
source venv/bin/activate
python -c "from app import create_app; app = create_app(); print('OK')"
```

### 8.2 数据库连接失败

```bash
# 测试数据库连接
mysql -u photo_user -p -h localhost photo_app

# 检查 MySQL 服务
sudo systemctl status mariadb
```

### 8.3 权限问题

```bash
# 修复上传目录权限
sudo chown -R root:root /opt/photo-app
sudo chmod -R 755 /opt/photo-app/uploads
```

---

## 附录：完整目录结构

```
/opt/photo-app/
├── app.py                 # Flask 应用入口
├── config.py              # 配置文件
├── extensions.py          # Flask 扩展
├── wsgi.py                # WSGI 入口
├── gunicorn.conf.py       # Gunicorn 配置
├── requirements-py36.txt  # Python 3.6 依赖
├── venv/                  # Python 虚拟环境
├── routes/                # API 路由
├── models/                # 数据模型
├── uploads/               # 上传文件目录
│   ├── backgrounds/
│   ├── composites/
│   ├── fonts/
│   └── temp/
└── logs/                  # 日志目录
    ├── access.log
    └── error.log
```
