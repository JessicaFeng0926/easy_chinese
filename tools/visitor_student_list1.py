from app.models import User
from app import create_app
import os

# 创建程序对象
app = create_app(os.environ.get('EC_CONFIG') or 'default')
# 激活程序上下文，在上下文中进行数据库查询
with app.app_context():
    all_visitor_student = User.query.filter_by(role_id=1,is_delete=False).all()+User.query.filter_by(role_id=2,is_delete=False).all()
    visitor_student_list1 = [[user.username,user.username] for user in all_visitor_student]