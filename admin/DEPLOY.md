# 后台管理系统部署文档

## 一、本地打包

```bash
cd admin
npm run build
```

打包后生成 `dist` 目录。

---

## 二、上传到服务器

```bash
# 创建目录
sudo mkdir -p /opt/photo-admin

# 上传 dist 目录（在本地执行）
scp -r ./dist/* user@your_server_ip:/opt/photo-admin/
```

---

## 三、配置 Nginx

### 3.1 创建 Nginx 配置文件

```bash
sudo cat > /etc/nginx/conf.d/photo-admin.conf << 'EOF'
server {
    listen 80;
    server_name your_server_ip;  # 替换为你的 IP 或域名

    # 管理后台静态文件目录
    root /opt/photo-admin;
    index index.html;

    # 上传文件大小限制
    client_max_body_size 50M;

    # 前端路由 - SPA 单页应用
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到后端服务
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # 上传的静态文件
    location /uploads/ {
        proxy_pass http://127.0.0.1:5001/uploads/;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    access_log /var/log/nginx/photo-admin-access.log;
    error_log /var/log/nginx/photo-admin-error.log;
}
EOF
```

### 3.2 测试并重启 Nginx

```bash
# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx
```

---

## 四、如果使用非 80 端口

如果 80 端口被占用，可以使用其他端口如 8080：

```bash
sudo cat > /etc/nginx/conf.d/photo-admin.conf << 'EOF'
server {
    listen 8080;
    server_name _;

    root /opt/photo-admin;
    index index.html;

    client_max_body_size 50M;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:5001/uploads/;
        expires 30d;
    }
}
EOF

# 开放防火墙端口
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# 重载 Nginx
sudo systemctl reload nginx
```

访问地址：`http://your_server_ip:8080`

---

## 五、常见问题

### 5.1 502 Bad Gateway

后端服务未启动，检查：
```bash
sudo systemctl status photo-app
sudo systemctl start photo-app
```

### 5.2 API 请求 404

检查 Nginx 配置中的 `proxy_pass` 路径是否正确。

### 5.3 上传文件失败

检查 `client_max_body_size` 配置是否足够大。

### 5.4 权限问题

```bash
sudo chown -R nginx:nginx /opt/photo-admin
sudo chmod -R 755 /opt/photo-admin
```

---

## 六、更新部署

```bash
# 1. 本地重新打包
npm run build

# 2. 上传到服务器
scp -r ./dist/* user@server:/opt/photo-admin/

# 3. 清除浏览器缓存或刷新
```
