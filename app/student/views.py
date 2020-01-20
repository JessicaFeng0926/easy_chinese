from flask import current_app,url_for,render_template,redirect,flash,request,jsonify
from flask_login import current_user,login_required
from . import student
from .forms import PersonalInfoForm,StudentRateForm
from ..models import User,Lesson,Order,MakeUpTime
import os
from ..import db
from datetime import datetime,timedelta
from pytz import country_timezones,timezone
import calendar
from calendar import monthcalendar,monthrange,Calendar

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

#学生选课
@student.route('/book_lesson')
@login_required
def book_lesson():
    '''这是学生订课的视图'''
    # 找到该学生的老师
    teacher = User.query.filter_by(id=current_user.student_profile.first().teacher_id).first()
    # 学生可能还没有分配老师，我们只操作分配了老师的情况
    if teacher:
        #取出老师的工作时间字符串并转化为列表 
        worktime=teacher.work_time.first().work_time
        worktime_list = worktime.split(';')

        #把以星期为单位的教师工作时间转化为UTC年月日小时的时间
        #第一步：构造出UTC的此时此刻
        cal = Calendar(6)  # 让每个星期都从星期天开始
        utc = timezone('UTC')
        utcnow = datetime.utcnow()
        utcnow = datetime(utcnow.year,utcnow.month,utcnow.day,utcnow.hour,tzinfo=utc)
        # 第二步：计算出可以选课的起始时间，也就是此时此刻的24小时后，以及截至时间，也就是现在开始的29天后
        available_start = utcnow+timedelta(1)
        available_end = utcnow + timedelta(29)
        # 第三步：找到起始日期和结束日期所在的星期，拼接出可以选课的28天的列表，
        # 大列表里的小列表代表一个个以周日开始的星期
        # 找起始日期所在的星期
        for i,week in enumerate(cal.monthdatescalendar(available_start.year,available_start.month)):
            if available_start.date() in week:
                start_index = i
                break
        # 先把目前确定的可以选课的这几个星期放进可选时间列表里
        all_available_dates = cal.monthdatescalendar(available_start.year,available_start.month)[start_index:]
        # 找到结束日期所在的星期
        for i,week in enumerate(cal.monthdatescalendar(available_end.year,available_end.month)):
            if available_end.date() in week:
                end_index = i
                break
        # 因为开始日期所在的那个月的日历和结束日期所在的那个月的日历可能有重复的星期
        # 所以我们要避免重复添加
        for week in cal.monthdatescalendar(available_end.year,available_end.month)[:end_index+1]:
            if week not in all_available_dates:
                all_available_dates.append(week)

        # 第四步：根据老师的工作时间，构造出以datetime对象为元素的列表
        # 创建一个空列表，存放老师的以小时为单位的工作时间
        new_worktime_list = []
        for week in all_available_dates:
            # w是类似于0-1这样的字符串，它表示星期天的UTC时间1点钟
            for w in worktime_list:
                date = week[int(w[0])]
                time = datetime(date.year,date.month,date.day,int(w[2:]),tzinfo=utc)
                if time<available_start or time>available_end:
                    continue
                new_worktime_list.append(time)
        # 第五步：把教师的特殊休息时间去掉
        special_rest_set = set()
        for data in teacher.special_rest.all():
            special_rest_set.add(datetime(data.rest_time.year,data.rest_time.month,data.rest_time.day,data.rest_time.hour,tzinfo=utc))
        for i in new_worktime_list[:]:
            if i in special_rest_set:
                new_worktime_list.remove(i)
        # 第六步：把教师的补班时间加进去(这一步要放在前面，因为可能补班的时间也被选上课了)
        makeup_time_list=[]
        for data in teacher.make_up_time.filter_by(expire=False).all():
            makeup_time_list.append(datetime(data.make_up_time.year,data.make_up_time.month,data.make_up_time.day,data.make_up_time.hour,tzinfo=utc))
        new_worktime_list+=makeup_time_list
        # 第七步：生成一个已预约的课程时间列表，并把这些时间从老师的工作时间里去掉
        # 为了节约资源，我们在查询的时候就筛选一下时间
        lessons = Lesson.query.filter(Lesson.teacher_id == teacher.id,Lesson.is_delete==False,Lesson.time>=datetime.utcnow()+timedelta(1)).all()
        # 先用set存放时间，因为查询比较快
        lessons_set = set()
        for lesson in lessons:
            time = lesson.time
            time = datetime(time.year,time.month,time.day,time.hour,tzinfo=utc)
            lessons_set.add(time)
        for i in new_worktime_list[:]:
            if i in lessons_set:
                new_worktime_list.remove(i)
        lessons_list = list(lessons_set)
        




    return render_template('student/book_lesson.html',teacher=teacher)