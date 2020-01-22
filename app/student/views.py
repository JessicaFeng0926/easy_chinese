from flask import current_app,url_for,render_template,redirect,flash,request,jsonify
from flask_login import current_user,login_required
from flask_sqlalchemy import Pagination
from . import student
from .forms import PersonalInfoForm,StudentRateForm
from ..models import User,Lesson,Order,MakeUpTime
import os
from ..import db
from datetime import datetime,timedelta
from pytz import country_timezones,timezone
import calendar
from calendar import monthcalendar,monthrange,Calendar
from tools.ectimezones import get_localtime

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
            # 还要把课时还到课时包里面
            # 我们要从最新的课时包开始，找到第一个不满(也就是left_amount<lesson_amount的课时包)，把还给学生的课加到这个包里
            all_packages = lesson.student.orders.filter(Order.pay_status=='paid').order_by(Order.id.desc()).all()
            for package in all_packages:
                if package.left_amount <package.lesson_amount:
                    package.left_amount += 1
                    break
            db.session.add(package)
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
        start_flag = False
        all_available_dates = []
        for week in cal.monthdatescalendar(available_start.year,available_start.month):
            # 在没找到起始日期所在的星期的时候，要检查这个星期是否就是我们寻找的
            if not start_flag and available_start.date() in week:
                start_flag = True
            # 从找到了起始日期所在的星期开始，我们要把它所在的以及它后面的星期加到列表里
            if start_flag:
                all_available_dates.append(week)
                
        # 遍历结束日期所在的月，如果当前星期不在列表里，就添加(因为前后两个月可能有重复的星期)
        # 遇到结束日期所在的星期，后面的就不用看了
        for week in cal.monthdatescalendar(available_end.year,available_end.month):
            if available_end not in week:
                all_available_dates.append(week)
            if available_end.date() in week:
                break
    

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
        
        #计算出游客的时区
        visitor_country=current_user.timezone
        if len(visitor_country)>2:
            visitor_tz = country_timezones[visitor_country[:2]][int(visitor_country[-1])]
        else:
            visitor_tz = country_timezones[visitor_country][0]
        tz_obj = timezone(visitor_tz)

        # 根据时区，生成游客视角的可以选课的28天的日历
        visitor_start = get_localtime(available_start,current_user)
        visitor_end = get_localtime(available_end,current_user)
        
        visitor_dates = []
        start_flag = False
        for week in cal.monthdatescalendar(visitor_start.year,visitor_start.month):
            # 因为遍历一个星期也会浪费时间，所以我们这里设两个条件
            # 如果flag已经是True了，就不需要再看结束日期在不在这个星期里了
            if not start_flag and visitor_start.date() in week:
                start_flag = True
            if start_flag:
                visitor_dates.append(week)
        # 因为前后两个月可能有重复的星期，所以要判断是否在列表里，不在的才添加
        for week in cal.monthdatescalendar(visitor_end.year,visitor_end.month):
            if week not in visitor_dates:
                visitor_dates.append(week)
            # 如果已经到了结束日期所在的星期，就不用看后面的了
            if visitor_end.date() in week:
                break
        
        # 获取页码
        page = request.args.get('page',1,type=int)
        # 如果有用户恶意修改页码，我们要把页码变成1
        if page>len(visitor_dates) or page<1:
            page = 1
        
        # 每个星期的月份和年，应该以这个星期中间的那一天为标准
        current_page = Pagination(visitor_dates,page,1,len(visitor_dates),visitor_dates[page-1])
        middle_day = current_page.items[3]
        month_name = calendar.month_name[middle_day.month]
        year = middle_day.year

        this_week = []
        only_dates = []

        for date in current_page.items:
            this_week.append('%s-%s-%s'%(date.year,date.month,date.day))
            only_dates.append(date.day)

        #把老师的可选的时间列表换成游客时区的时间(字符串)
        for i,time in enumerate(new_worktime_list):
            time=time.astimezone(tz_obj)
            new_worktime_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        #把老师有课的时间转换成游客时区的时间（字符串）
        for i,time in enumerate(lessons_list):
            time=time.astimezone(tz_obj)
            lessons_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        
        # 查看并处理选课的ajax请求
        time = request.args.get('time','',type=str)
        if time:
            time = time.split('-')
            #先构造一个没有时区的datetime对象
            time = datetime(int(time[0]),int(time[1]),int(time[2]),int(time[3]))
            #再把它变成时区为游客所在地区的datetime对象
            time = tz_obj.localize(time)
            #再把时区变成utc时区
            time = time.astimezone(utc)

            # 再判断一次是否在可选时间范围内
            if time>=available_start:
                # 看看学生的课时包里是否还有课
                active_package = current_user.orders.filter(Order.pay_status=='paid',Order.left_amount>0).order_by(Order.id.asc()).first()
                if active_package:
                    # 课时包的课程数量扣掉一节
                    active_package.left_amount -= 1
                    db.session.add(active_package)
                    # 把选课信息存进数据库
                    lesson = current_user.lessons.filter(Lesson.time==time,Lesson.teacher_id==teacher.id).first()
                    if lesson:
                        lesson.is_delete = False
                    else:
                        lesson = Lesson()
                        lesson.student_id = current_user.id
                        lesson.teacher_id = teacher.id
                        lesson.time = time
                        lesson.message = ''
                        lesson.lesson_type =active_package.lesson_type
                    db.session.add(lesson)
                    return jsonify({'status':'ok','msg':"You've successfully booked a lesson."})
                else:
                    return jsonify({'status':'fail','msg':"You don't have any lessons now. Please buy another package."})
            else:
                return jsonify({'status':'fail','msg':'You need to book lessons not earlier than 24 hours from now.'})
        return render_template('student/book_lesson.html',
        teacher=teacher,
        this_week=this_week,
        only_dates=only_dates,
        new_worktime_list=new_worktime_list,
        month_name=month_name,
        year=year,
        current_page=current_page,
        lessons_list=lessons_list)

    return render_template('student/book_lesson.html',teacher=teacher)