#!/usr/bin/env python3
"""
添加 ai_quota 和 ai_used 字段到 users 表
"""

import pymysql

# MySQL 配置
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'photo_app',
    'charset': 'utf8mb4'
}

print("连接 MySQL 数据库...")

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("DESCRIBE users")
    columns = [col[0] for col in cursor.fetchall()]
    print(f"现有字段: {columns}")
    
    # 添加 ai_quota 字段
    if 'ai_quota' not in columns:
        print("添加 ai_quota 字段...")
        cursor.execute("ALTER TABLE users ADD COLUMN ai_quota INT DEFAULT 200")
        print("ai_quota 字段添加成功")
    else:
        print("ai_quota 字段已存在")
    
    # 添加 ai_used 字段
    if 'ai_used' not in columns:
        print("添加 ai_used 字段...")
        cursor.execute("ALTER TABLE users ADD COLUMN ai_used INT DEFAULT 0")
        print("ai_used 字段添加成功")
    else:
        print("ai_used 字段已存在")
    
    conn.commit()
    conn.close()
    
    print("数据库更新完成！")
    
except Exception as e:
    print(f"错误: {e}")
