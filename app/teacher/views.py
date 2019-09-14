from flask import render_template,request,current_app,redirect,url_for,flash
from flask_login import current_user,login_required
from . import teacher
from .forms import PersonalInfoForm
from pytz import timezone,country_timezones
from datetime import datetime
from ..models import User,Lesson
from .. import db
import os

#教师个人信息
@teacher.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''这是个人信息的视图'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        user.name = form.name.data
        user.location = form.location.data
        user.timezone = form.timezone.data
        if 'image' in request.files:
            file = request.files['image']
            if file:
                UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
                cleaned_filename = User.validate_image(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER,cleaned_filename))
                user.image = cleaned_filename
        db.session.add(user)
        flash('Successfully modified your personal information')
        return redirect(url_for('teacher.personal_info'))
    form.email.data = current_user.email
    form.username.data = current_user.username
    form.name.data = current_user.name
    form.image.data = current_user.image
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    #用户的注册时间在数据库里是一个utc的datetime对象，但是并没有tzinfo
    #所以这里要先构造成tzinfo为utc的datetime对象，再转化为tzinfo为学生时区的datetime对象
    utc = timezone('UTC')
    if len(current_user.timezone) > 2:
        user_tz = country_timezones[current_user.timezone[:2]][int(current_user.timezone[3:])]
    else:
        user_tz = country_timezones[current_user.timezone][0]
    user_tz = timezone(user_tz)
    time = current_user.member_since
    utc_member_since = datetime(time.year,time.month,time.day,time.hour,time.minute,time.second,tzinfo=utc)
    local_member_since = utc_member_since.astimezone(user_tz)
    form.member_since.data = local_member_since.strftime('%Y-%m-%d')
    return render_template('teacher/personal_info.html',form=form)

#我的所有学生
@teacher.route('my_students')
@login_required
def my_students():
    '''这是我的所有学生的视图'''
    username = request.args.get('username','',type=str)
    student = []
    lessons = []
    tab = request.args.get('tab','',type=str)
    #如果有用户名，就要查看某个学生的信息，否则就查看该教师的所有学生
    if username:
        student = User.query.filter_by(username=username).first()
        if tab == 'lessons':
            lessons = student.lessons.order_by(Lesson.time.asc()).all()
            tz = current_user.timezone
            if len(tz) == 2:
                tz = country_timezones[tz][0]
            else:
                tz = country_timezones[tz[:2]][int(tz[3:])]
            tz = timezone(tz)
            utc = timezone('UTC')
            #给每节课添加教师信息，以及根据教师时区转化出的教师当地的上课时间
            for lesson in lessons:
                teacher = User.query.get(lesson.teacher_id)
                lesson.teacher = teacher
                utctime = datetime(lesson.time.year,lesson.time.month,lesson.time.day,lesson.time.hour,tzinfo=utc)
                localtime = utctime.astimezone(tz)
                lesson.localtime = localtime
        elif tab == 'profile':
            pass
    return render_template('teacher/my_students.html',username=username,student=student,tab=tab,lessons=lessons)

