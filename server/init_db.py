"""数据库初始化脚本"""
import os
import pymysql
from config import Config

def create_database():
    """创建数据库（如果不存在）"""
    password = Config.MYSQL_PASSWORD

    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS %s CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % Config.MYSQL_DATABASE)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ 数据库连接成功！")
        print("✅ 数据库 '%s' 已创建/确认存在" % Config.MYSQL_DATABASE)
        return password

    except pymysql.Error as e:
        print("❌ 数据库连接失败: %s" % e)
        print("   请检查 .env 中的 MYSQL_USER / MYSQL_PASSWORD")
        return None


def init_admin():
    """创建管理员账户"""
    from app import create_app, db
    from models import User
    
    app = create_app()
    with app.app_context():
        # 检查是否已有管理员
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@photo.app',
                role='admin'
            )
            admin.set_password(os.environ.get('ADMIN_INIT_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            print("✅ 管理员账户已创建")
            print("   用户名: admin")
        else:
            print("ℹ️  管理员账户已存在")


if __name__ == '__main__':
    if create_database():
        init_admin()
        print("\n🎉 数据库初始化完成！")
