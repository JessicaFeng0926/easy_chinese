from . import moderator

from flask import url_for,render_template,redirect,request
from flask_login import current_user,login_required
from .. models import User,Order,Lesson
from .forms import AssignTeacherForm
from app import db
from tools.ectimezones import get_localtime


# 给还没有老师的新生分配老师
@moderator.route('/assign_teacher/<username>',methods=['GET','POST'])
@login_required
def assign_teacher(username):
    '''这是给新生分配老师的视图

    :参数 username:学生的用户名
    '''
    student = User.query.filter_by(username=username).first()
    if student:
        form = AssignTeacherForm()
        if form.validate_on_submit():
            teacher_username = form.primary_teacher.data
            teacher = User.query.filter_by(username=teacher_username).first()
            teacher_id = teacher.id
            student_profile = student.student_profile.first()
            student_profile.teacher_id = teacher_id
            db.session.add(student_profile)
            return redirect(url_for('main.personal_center'))
        form.username.data = username
        old_teacher_ids = student.orders.filter_by(pay_status='paid').order_by(Order.pay_time.asc()).first().past_teachers
        if old_teacher_ids:
            old_teacher_ids_list = old_teacher_ids.split(';')
            past_teachers_names = User.query.get(old_teacher_ids_list[0]).name
            for oid in old_teacher_ids_list[1:]:
                past_teachers_names=past_teachers_names+';'+User.query.get(oid).name
            form.old_teachers.data = past_teachers_names
        return render_template('moderator/assign_teacher.html',form=form) 


# 查看学生的课程列表以及个人信息
@moderator.route('/show_student_profile/<username>')
@login_required
def show_student_profile(username):
    '''这是查看学生的课程列表以及个人信息的视图'''
    student = User.query.filter_by(username=username).first()
    if student:
        tab = request.args.get('tab','',type=str)
        if tab == 'lessons':
            lessons = student.lessons.filter_by(is_delete=False).order_by(Lesson.time.desc()).all()
            for lesson in lessons:
                lesson.teacher = User.query.get(lesson.teacher_id)
                lesson.localtime = get_localtime(lesson.time,current_user)
            return render_template('moderator/student_profile.html',student=student,tab=tab,lessons=lessons,username=username)
        elif tab == 'profile':
            teacher_id = student.student_profile.first().teacher_id
            if teacher_id:
                student.teacher = User.query.get(teacher_id)
            else:
                student.teacher = None
            student.localsince = get_localtime(student.member_since,current_user)
            return render_template('moderator/student_profile.html',student=student,tab=tab,username=username)

# 查看学生某节课的课程记录
@moderator.route('/check_detail/<lesson_id>')
@login_required
def check_detail(lesson_id):
    '''这是协管员查看某节课的课程记录的视图'''
    lesson = Lesson.query.get_or_404(lesson_id)
    status_dict = {'Complete':'正常完成','Tea Absent':'教师缺勤','Stu Absent':'学生缺勤','Tea Late':'教师迟到'}
    #添加中文描述的课时完成状态
    lesson.c_status = status_dict[lesson.status]
    #添加本节课的教师对象
    teacher = User.query.get(lesson.teacher_id)
    lesson.teacher = teacher
    #添加用户以用户时区为标准的上课时间对象
    lesson.localtime = get_localtime(lesson.time,current_user)
    record = lesson.lesson_record.first()
    return render_template('moderator/check_detail.html',lesson=lesson,record=record)        

# 显示全校学生名单
@moderator.route('/check_students')
@login_required
def check_students():
    '''这是显示全校学生名单的页面'''
    students = User.query.filter_by(role_id=2,is_delete=False).order_by(User.username.asc()).all()
    all_students = []
    count = 0
    temp = []
    for student in students:
        temp.append(student)
        count += 1
        if count == 4:
            all_students.append(temp)
            temp = []
            count = 0
    if temp:
        all_students.append(temp)


    return render_template('moderator/check_students.html',all_students=all_students)






