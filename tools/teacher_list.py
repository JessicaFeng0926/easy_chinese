from app.models import User
from app import create_app
import os

# 创建程序对象
app = create_app(os.environ.get('EC_CONFIG') or 'default')
# 激活程序上下文，在上下文中进行数据库查询
with app.app_context():
    all_teachers = User.query.filter_by(role_id=3,is_delete=False).all()
    teacher_list = [[teacher.username,teacher.name] for teacher in all_teachers]