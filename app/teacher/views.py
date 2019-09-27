from flask import render_template,request,current_app,redirect,url_for,flash
from flask_login import current_user,login_required
from . import teacher
from .forms import PersonalInfoForm,EditProfileForm,RecordLessonForm
from pytz import timezone,country_timezones
from datetime import datetime
from ..models import User,Lesson,StudentProfile,LessonRecord
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
@teacher.route('/my_students')
@login_required
def my_students():
    '''这是我的所有学生的视图'''
    username = request.args.get('username','',type=str)
    student = []
    lessons = []
    primary_teacher = []
    tab = request.args.get('tab','',type=str)
    #如果有用户名，就要查看某个学生的信息，否则就查看该教师的所有学生
    if username:
        student = User.query.filter_by(username=username).first()
        tz = current_user.timezone
        if len(tz) == 2:
            tz = country_timezones[tz][0]
        else:
            tz = country_timezones[tz[:2]][int(tz[3:])]
        tz = timezone(tz)
        utc = timezone('UTC')
        #查看该学生的所有课程
        if tab == 'lessons':
            lessons = student.lessons.order_by(Lesson.time.asc()).all()
            
            #给每节课添加教师信息，以及根据教师时区转化出的教师当地的上课时间
            for lesson in lessons:
                teacher = User.query.get(lesson.teacher_id)
                lesson.teacher = teacher
                utctime = datetime(lesson.time.year,lesson.time.month,lesson.time.day,lesson.time.hour,tzinfo=utc)
                localtime = utctime.astimezone(tz)
                lesson.localtime = localtime
        #查看该学生的个人信息
        elif tab == 'profile':
            member_since = student.member_since
            utcsince = datetime(member_since.year,member_since.month,member_since.day,member_since.hour,tzinfo=utc)
            localsince = utcsince.astimezone(tz)
            student.localsince = localsince
            teacher_id = student.student_profile.first().teacher_id
            primary_teacher = User.query.get(teacher_id)
        return render_template('teacher/my_students.html',username=username,student=student,tab=tab,lessons=lessons,primary_teacher=primary_teacher)
    #如果没有用户名，那就查询我的所有学生
    student_profiles = StudentProfile.query.filter_by(teacher_id=current_user.id).all()
    students=[]
    for profile in student_profiles:
        students.append(profile.student)
    return render_template('teacher/my_students.html',students=students)

#修改主管学生信息
@teacher.route('/edit_profile/<username>',methods=['GET','POST'])
@login_required
def edit_profile(username):
    '''修改主管学生信息'''
    student = User.query.filter_by(username=username,role_id=2).first()
    if student:
        utc = timezone('UTC')
        tz = current_user.timezone
        if len(tz) == 2:
            tz = country_timezones[tz][0]
        else:
            tz = country_timezones[tz[:2]][int(tz[3:])]
        tz = timezone(tz)
        member_since = student.member_since
        utcsince = datetime(member_since.year,member_since.month,member_since.day,member_since.hour,tzinfo=utc)
        localsince = utcsince.astimezone(tz)
        student.localsince = localsince
    student_profile = student.student_profile.first()
    form = EditProfileForm()
    if form.validate_on_submit():
        student_profile.nickname = form.nickname.data
        student_profile.gender = form.gender.data
        student_profile.age = form.age.data
        student_profile.job = form.job.data
        student_profile.family = form.family.data
        student_profile.personality = form.personality.data
        student_profile.hobby = form.hobby.data
        student_profile.taboo = form.taboo.data
        student_profile.reason = form.reason.data
        student_profile.goal = form.goal.data
        student_profile.level = form.level.data
        student_profile.ability = form.ability.data
        student_profile.notes = form.notes.data
        student_profile.homework = form.homework.data
        student_profile.teacher_phone = form.teacher_phone.data
        db.session.add(student_profile)
        flash("主管学生信息修改成功！")
        return redirect(url_for('teacher.my_students',username=username,tab='profile'))

    if student_profile:
        form.nickname.data = student_profile.nickname
        form.gender.data = student_profile.gender
        form.age.data = student_profile.age
        form.job.data = student_profile.job
        form.family.data = student_profile.family
        form.personality.data = student_profile.personality
        form.hobby.data = student_profile.hobby
        form.taboo.data = student_profile.taboo
        form.reason.data = student_profile.reason
        form.goal.data = student_profile.goal
        form.level.data = student_profile.level
        form.ability.data = student_profile.ability
        form.notes.data = student_profile.notes
        form.homework.data = student_profile.homework
        form.teacher_phone.data = student_profile.teacher_phone

    return render_template('teacher/edit_profile.html',student=student,form=form)

#填写课程详情
@teacher.route('/record_lesson/<int:id>',methods=['GET','POST'])
@login_required
def record_lesson(id):
    '''这是填写课程详情的视图'''
    lesson = Lesson.query.get_or_404(id)
    form = RecordLessonForm()
    record = lesson.lesson_record.first() or LessonRecord()
    if not record.lesson_id:
        record.lesson_id = lesson.id
    if form.validate_on_submit():
        record.talk = form.talk.data
        record.this_lesson = form.this_lesson.data
        record.next_lesson = form.next_lesson.data
        record.homework = form.homework.data
        record.textbook = form.textbook.data
        record.other = form.other.data
        lesson.status = form.status.data
        lesson.t_comment = form.t_comment.data
        db.session.add(record)
        db.session.add(lesson)
        return redirect(url_for('main.personal_center'))
    
    form.talk.data = record.talk
    form.this_lesson.data = record.this_lesson
    form.next_lesson.data = record.next_lesson
    form.homework.data = record.homework
    form.textbook.data = record.textbook
    form.other.data = record.other
    form.status.data = lesson.status
    form.t_comment.data = lesson.t_comment
   
    
    return render_template('teacher/record_lesson.html',form=form)

#查看课程详情
@teacher.route('/check_detail/<int:id>',methods=['GET','POST'])
@login_required
def check_detail(id):
    '''查看课程详情'''
    lesson = Lesson.query.get_or_404(id)
    status_dict = {'Complete':'正常完成','Tea Absent':'教师缺勤','Stu Absent':'学生缺勤','Tea Late':'教师迟到'}
    #添加中文描述的课时完成状态
    lesson.c_status = status_dict[lesson.status]
    #添加本节课的教师对象
    teacher = User.query.get(lesson.teacher_id)
    lesson.teacher = teacher
    #添加用户以用户时区为标准的上课时间对象
    utc = timezone('UTC')
    tz = current_user.timezone
    if len(tz) == 2:
        tz = country_timezones[tz][0]
    else:
        tz = country_timezones[tz[:2]][int(tz[3:])]
    tz = timezone(tz)
    time = lesson.time
    utctime = datetime(time.year,time.month,time.day,time.hour,tzinfo=utc)
    localtime = utctime.astimezone(tz)
    lesson.localtime = localtime
    record = lesson.lesson_record.first()
    return render_template('teacher/check_detail.html',lesson=lesson,record=record)