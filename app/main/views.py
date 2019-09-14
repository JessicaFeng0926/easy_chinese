from flask import request,render_template,url_for,redirect
from . import main
from flask_login import login_required,current_user
from ..models import User,Lesson
from pytz import timezone,country_timezones
from datetime import datetime,timedelta

@main.route('/')
def index():
    #把主页需要的教师信息传过去
    teacher_list=User.query.filter(User.role_id==3,User.name!=None).all()[:3]
    return render_template('index.html',teacher_list=teacher_list)

@main.route('/personal_center')
@login_required
def personal_center():
    '''这是个人中心的视图，不同角色会显示不同的页面'''
    if current_user.role.name == 'Visitor':
        #查询该游客是否定过试听课
        trial_lessons = Lesson.query.filter_by(student_id=current_user.id,lesson_type='Trial').all()
        #如果定过试听课
        if trial_lessons:
            #获取游客的时区信息
            if len(current_user.timezone)==2:
                tz=country_timezones[current_user.timezone][0]
                tz=timezone(tz)
            else:
                tz=country_timezones[current_user.timezone[:2]][int(current_user.timezone[3:])]
                tz=timezone(tz)
            utc = timezone('UTC')
            #把试听课的时间转化为游客当地的时间，同时也查询出老师的对象，然后把时间和教师信息都附加到每节试听课对象上
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
        #查询出24小时内老师的未开始课程
        lessons = Lesson.query.filter_by(teacher_id = current_user.id,status ='Not started').order_by(Lesson.time.asc()).all()
        if lessons :
            lesson_list = []
            utcnow = datetime.utcnow()
            utc = timezone('UTC')
            #获取老师的时区信息（是国家代码和数字的组合,比如CN-0）
            tz = current_user.timezone
            if len(tz)==2:
                #获取具体的时区代码，比如Asia/Shanghai
                tz = country_timezones[tz][0]
            else:
                tz = country_timezones[tz[:2]][int(tz[3:])]
            #获取时区对象
            tz = timezone(tz)
                

            for lesson in lessons:
                #如果课程的时间距离现在已经大于24小时了，就跳出循环
                if lesson.time > utcnow+timedelta(1):
                    break
                #在24小时内的课都添加到列表里
                utctime = datetime(lesson.time.year,lesson.time.month,lesson.time.day,lesson.time.hour,tzinfo=utc)
                localtime = utctime.astimezone(tz)
                lesson.localtime = localtime
                lesson_list.append(lesson)
    
        
        return render_template('teacher/homepage.html',lesson_list=lesson_list)
    elif current_user.role.name == 'Moderator':
        return render_template('moderator/homepage.html')
    elif current_user.role.name == 'Administrator':
        return render_template('admin/homepage.html')
    
