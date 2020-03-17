from . import administrator

from flask import url_for,render_template,redirect,request,flash,jsonify
from flask_login import login_required,current_user
from .forms import AssignTeacherForm
from tools.ectimezones import get_localtime
from app import db
from ..models import User,Order


# 管理员的个人信息
@administrator.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''管理员的个人信息'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        user.name = form.name.data
        user.location = form.location.data
        user.timezone = form.timezone.data
        db.session.add(user)
        flash('成功修改个人信息')
        return redirect(url_for('administrator.personal_info'))
    form.email.data = current_user.email
    form.username.data = current_user.username
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    local_member_since = get_localtime(current_user.member_since,current_user)
    form.member_since.data = local_member_since.strftime('%Y-%m-%d')
    return render_template('administrator/personal_info.html',form=form)

# 给还没有老师的新生分配老师
@administrator.route('/assign_teacher/<username>',methods=['GET','POST'])
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
        return render_template('administrator/assign_teacher.html',form=form) 