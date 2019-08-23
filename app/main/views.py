from flask import request,render_template,url_for,redirect
from . import main
from flask_login import login_required,current_user

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/personal_center/<username>')
@login_required
def personal_center(username):
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
    
