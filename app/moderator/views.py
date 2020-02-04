from . import moderator

from flask import url_for,render_template,redirect,request,flash
from flask_login import current_user,login_required
from .. models import User,Order,Lesson
from .forms import AssignTeacherForm,ChangeTeacherForm
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
        # 学生的第一个订单里保存了过去的老师
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

# 显示全校学生名单,为检查学生的详细信息做准备
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

# 显示全校学生名单，为更换老师做准备
@moderator.route('/pre_change_teacher')
@login_required
def pre_change_teacher():
    '''显示全校学生名单，点进去就可以给当前学生换老师'''
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
    
    return render_template('moderator/pre_change_teacher.html',all_students=all_students)

# 给在校生更换老师
@moderator.route('/change_teacher/<username>',methods=['GET','POST'])
@login_required
def change_teacher(username):
    '''这是给具体的学生更换主管老师的视图
    :参数 username:学生的用户名
    '''
    student = User.query.filter_by(username=username,is_delete=False).first()
    if student:
        form = ChangeTeacherForm()
        # 获取学生的第一个订单，因为那里面保存了一些过去的老师
        first_order = student.orders.filter_by(pay_status='paid').order_by(Order.pay_time.asc()).first()
        # 获取学生的简历
        student_profile = student.student_profile.first()
        if form.validate_on_submit():
            new_teacher_username = form.new_teacher.data
            new_teacher_id = User.query.filter_by(username=new_teacher_username).first().id
            current_teacher_id = student_profile.teacher_id
            if int(new_teacher_id) == current_teacher_id:
                flash('新主管老师和现任主管老师不可以是同一人')
                return redirect(url_for('moderator.change_teacher',username=username))
            # 得到过去老师的集合
            past_teacher_str = first_order.past_teachers
            # 如果没有过去的老师，直接把当前老师加入到过去的老师字符串里
            if past_teacher_str is None:
                first_order.past_teachers = str(current_teacher_id)
                db.session.add(first_order)
            # 如果有过去的老师
            else:
                past_teacher_set = set(past_teacher_str.split(';'))
                # 如果当前的主管老师不在过去的老师里，就把当前主管老师加入到过去教师名单里
                if str(current_teacher_id) not in past_teacher_set:
                    first_order.past_teachers = first_order.past_teachers+';'+str(current_teacher_id)
                    db.session.add(first_order)
            # 修改学生的主管老师
            student_profile.teacher_id = int(new_teacher_id)
            # 把新的学生简历提交到数据库
            db.session.add(student_profile)
            # 重定向
            return redirect(url_for('moderator.pre_change_teacher'))
        form.username.data = username
        form.current_teacher.data = User.query.get(student.student_profile.first().teacher_id).name
        # 学生的第一个订单里保存了过去的老师
        old_teacher_ids = first_order.past_teachers
        if old_teacher_ids:
            old_teacher_ids_list = old_teacher_ids.split(';')
            past_teachers_names = User.query.get(old_teacher_ids_list[0]).name
            for oid in old_teacher_ids_list[1:]:
                past_teachers_names=past_teachers_names+';'+User.query.get(oid).name
            form.old_teachers.data = past_teachers_names
        return render_template('moderator/change_teacher.html',form=form)