from flask import request,render_template,url_for,redirect
from . import main
from flask_login import login_required,current_user
from ..models import User,Lesson
from pytz import timezone,country_timezones
from datetime import datetime

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
        trial_lessons = Lesson.query.filter_by(student_id=current_user.id,lesson_type='Trial').all()
        if trial_lessons:
            if len(current_user.timezone)==2:
                tz=country_timezones[current_user.timezone][0]
                tz=timezone(tz)
            else:
                tz=country_timezones[current_user.timezone[:2]][int(current_user.timezone[3:])]
                tz=timezone(tz)
            utc = timezone('UTC')
            for lesson in trial_lessons:
                utctime=datetime(lesson.time.year,lesson.time.month,lesson.time.day,lesson.time.hour,tzinfo=utc)
                localtime=utctime.astimezone(tz)
                localtime='%s-%s-%s %s:00'%(localtime.year,localtime.month,localtime.day,localtime.hour)
                lesson.localtime=localtime
                teacher=User.query.get(lesson.teacher_id)
                lesson.teacher=teacher

        return render_template('visitor/homepage.html',trial_lessons=trial_lessons)
    elif current_user.role.name == 'Student':
        return render_template('student/homepage.html')
    elif current_user.role.name == 'Teacher':
        return render_template('teacher/homepage.html')
    elif current_user.role.name == 'Moderator':
        return render_template('moderator/homepage.html')
    elif current_user.role.name == 'Administrator':
        return render_template('admin/homepage.html')
    
