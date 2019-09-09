from flask import request,render_template,url_for,redirect
from . import main
from flask_login import login_required,current_user
from ..models import User

@main.route('/')
def index():
    #把主页需要的教师信息传过去
    teacher_list=User.query.filter_by(role_id=3).all()[:3]
    return render_template('index.html',teacher_list=teacher_list)

@main.route('/personal_center')
@login_required
def personal_center():
    '''这是个人中心的视图，不同角色会显示不同的页面'''
    if current_user.role.name == 'Visitor':
        return render_template('visitor/homepage.html')
    elif current_user.role.name == 'Student':
        return render_template('student/homepage.html')
    elif current_user.role.name == 'Teacher':
        return render_template('teacher/homepage.html')
    elif current_user.role.name == 'Moderator':
        return render_template('moderator/homepage.html')
    elif current_user.role.name == 'Administrator':
        return render_template('admin/homepage.html')
    
