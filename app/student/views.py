from flask import current_app,url_for,render_template,redirect,flash,request,jsonify
from flask_login import current_user,login_required
from . import student
from .forms import PersonalInfoForm,StudentRateForm
from ..models import User,Lesson,Order
import os
from ..import db
from datetime import datetime
from pytz import country_timezones,timezone

#个人信息
@student.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''这是学生的个人信息视图'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user=current_user._get_current_object()
        user.name = form.name.data
        user.location = form.location.data
        user.timezone = form.timezone.data
        if 'image' in request.files:
            file = request.files['image']
            if file:
                cleaned_filename=User.validate_image(file.filename)
                UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
                file.save(os.path.join(UPLOAD_FOLDER,cleaned_filename))
                user.image = cleaned_filename
        db.session.add(user)
        flash('Successfully modified your personal information')
        return redirect(url_for('student.personal_info'))

    form.image.data = current_user.image
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.member_since.data = current_user.member_since.strftime('%Y-%m-%d')
    return render_template('student/personal_info.html',form=form)

#取消已选课程
@student.route('/cancel')
@login_required
def cancel():
    '''取消相应的课程'''
    id = request.args.get("id",0,type=int)
    if id:
        lesson=Lesson.query.get_or_404(id)
        #还要看看时间是不是超过10分钟
        if (lesson.time-datetime.utcnow()).seconds >= 600:
            lesson.is_delete=True
            db.session.add(lesson)
            return jsonify({'status':'ok'})
        return jsonify({"status":"fail"})
    return jsonify({'status':'fail'})

#给课程评分
@student.route('/rate/<lesson_id>',methods=['GET','POST'])
@login_required
def rate(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if current_user.id != lesson.student_id:
        flash("You can not rate a lesson that does not belong to you.")
        return redirect(url_for("main.personal_center"))
    form = StudentRateForm()
    if form.validate_on_submit():
        lesson.mark = int(form.mark.data)
        lesson.s_comment = form.s_comment.data
        db.session.add(lesson)
        flash("Rated successfully!")
        return redirect(url_for("main.personal_center"))
    flash("You'd better double check before you submit your rating ,because you're not allowed to modify it.")
    return render_template('student/student_rate.html',form=form)
    
#我的课时包
@student.route('/my_packages')
@login_required
def my_packages():
    '''
    这是学生的所有课时包页面
    '''
    #这是未付款的课时包
    new_orders=current_user.orders.filter(Order.pay_status=='waiting').order_by(Order.id.desc()).all()
    for order in new_orders:
        order.teacher=User.query.get(order.teacher_id)
    #下面是已付款的课时包
    old_orders = current_user.orders.filter(Order.pay_status=='paid').order_by(Order.id.desc()).all()
    #学生的时区
    tz=current_user.timezone
    if len(tz)==2:
        tz = country_timezones[tz][0] 
    else:
        tz = country_timezones[tz[:2]][int(tz[3:])]
    tz = timezone(tz)
    utc = timezone('UTC')
    for order in old_orders:
        order.teacher=User.query.get(order.teacher_id)
        start = datetime(order.pay_time.year,order.pay_time.month,order.pay_time.day,order.pay_time.hour,tzinfo=utc)
        local_start = start.astimezone(tz)
        order.local_start = local_start
        end = datetime(order.end_time.year,order.end_time.month,order.end_time.day,order.end_time.hour,tzinfo=utc)
        local_end = end.astimezone(tz)
        order.local_end = local_end
    return render_template('student/my_packages.html',new_orders=new_orders,old_orders=old_orders)