from . import visitor
from flask import render_template,url_for,current_app,request,flash,redirect,jsonify
from flask_login import current_user,login_required
from . forms import PersonalInfoForm
import os
from .. import db
from ..models import User,Lesson,Order
from pytz import country_timezones,timezone
from datetime import datetime,timedelta
import calendar
from calendar import monthcalendar,monthrange,Calendar
from flask_sqlalchemy import Pagination


#游客个人信息路由和视图
@visitor.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''这是修改个人信息的视图'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user=current_user._get_current_object()
        user.name=form.name.data
        user.location=form.location.data
        user.timezone=form.timezone.data
        if 'image' in request.files:
            file = request.files['image']
            if file:
                cleaned_filename = User.validate_image(file.filename)
                UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
                file.save(os.path.join(UPLOAD_FOLDER,cleaned_filename))
                user.image=cleaned_filename
        db.session.add(user)
        flash('Successfully modified your personal information')
        return redirect(url_for('visitor.personal_info'))


    form.image.data=current_user.image
    form.username.data=current_user.username
    form.email.data=current_user.email
    form.name.data=current_user.name
    form.location.data=current_user.location
    form.member_since.data=current_user.member_since.strftime('%Y-%m-%d')
    form.timezone.data=current_user.timezone
    return render_template('visitor/personal_info.html',form=form)

#游客预订试听课
@visitor.route('/trial/<username>',methods=['GET','POST'])
@login_required
def trial(username):
    '''
    游客预订试听课的视图

    :参数 username:要订课的老师的用户名
    '''
    teacher=User.query.filter_by(username=username).first()
    if teacher:   
        #取出老师的工作时间字符串并转化为列表 
        worktime=teacher.work_time.first().work_time
        worktime_list = worktime.split(';')


        #把以星期为单位的老师工作时间转化为以UTC的年月日小时为单位的工作时间
        #第一步：构造出utc的此时此刻
        cal = Calendar(6)
        utc=timezone('UTC')
        utcnow = datetime.utcnow()
        utcnow = datetime(utcnow.year,utcnow.month,utcnow.day,utcnow.hour,tzinfo=utc)
        #第二步：计算出可以选课的起始时间，也就是utcnow的24小时后，和截止时间，也就是utcnow的29天后
        available_start = utcnow+timedelta(1)
        available_end = utcnow+timedelta(29)
        #第三步：找到起始日期所在的星期、结束日期所在的星期，并拼接出包含可以选课的28天的日期列表，列表里的每个元素是一个子列表，子列表是一个以周日开始的星期
        #找出开始日期所在的星期
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

        #第四步：根据老师的工作时间，构造出以datetime对象为元素的列表
        #这就是我们最终需要的老师以小时为单位的工作时间列表
        new_worktime_list=[]
        for week in all_available_dates:
            for w in worktime_list:
                date = week[int(w[0])]
                time = datetime(date.year,date.month,date.day,int(w[2:]),tzinfo=utc)
                if time < available_start or time > available_end:
                    continue
                new_worktime_list.append(time)
        #第五步：把教师的特殊休息时间从列表中去除
        special_rest_list = []
        for data in teacher.special_rest.all():
            special_rest_list.append(datetime(data.rest_time.year,data.rest_time.month,data.rest_time.day,data.rest_time.hour,tzinfo=utc))
        for i in new_worktime_list[:]:
            if i in special_rest_list:
                new_worktime_list.remove(i)
        #第六步：把教师的补班时间加到列表里（这一步放在前面，因为可能补班的时间也被选上课了）
        makeup_time_list=[]
        for data in teacher.make_up_time.filter_by(expire=False).all():
            makeup_time_list.append(datetime(data.make_up_time.year,data.make_up_time.month,data.make_up_time.day,data.make_up_time.hour,tzinfo=utc))
        new_worktime_list+=makeup_time_list
        #第七步：生成一个已预约的课程时间列表,并把这些时间点从老师的工作时间表中去掉
        lessons = Lesson.query.filter_by(teacher_id = teacher.id,is_delete=False).all()
        #已预约的课程时间列表
        lessons_list = []
        for lesson in lessons:
            time = lesson.time
            time = datetime(time.year,time.month,time.day,time.hour,tzinfo=utc)
            #只关心那些在可选时间范围内的课程
            if time >= available_start:
                lessons_list.append(time)
        for i in new_worktime_list[:]:
            if i in lessons_list:
                new_worktime_list.remove(i)
        
        

        #计算出游客的时区
        visitor_country=current_user.timezone
        if len(visitor_country)>2:
            visitor_tz = country_timezones[visitor_country[:2]][int(visitor_country[-1])]
        else:
            visitor_tz = country_timezones[visitor_country][0]
        tz_obj = timezone(visitor_tz)
        
        #根据时区，生成游客的包含可以选课的28天的日历
        visitor_start = datetime(available_start.year,available_start.month,available_start.day,available_start.hour,tzinfo=tz_obj)
        visitor_end = datetime(available_end.year,available_end.month,available_end.day,available_end.hour,tzinfo=tz_obj)

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
        #如果有用户恶意修改page的数值，使得page超过了我们能接收的范围，我们就是手动让它重新等于1
        if page > len(visitor_dates) or page<1:
            page = 1
        
        #每个星期的月份和年份应当以每个星期中间的那一天为标准
        current_page=Pagination(visitor_dates,page,1,len(visitor_dates),visitor_dates[page-1])
        middle_day = current_page.items[3]
        month_name = calendar.month_name[middle_day.month]
        year = middle_day.year

        this_week=[]
        only_dates=[]
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

        #查看并处理选课的ajax请求
        time = request.form.get('time','',type=str)
        message = request.form.get('message','',type=str)
        if time and message:
            #如果该游客已经有一节试听课记录了，并且那节试听课是完成或者还未开始的状态，不允许他再次选择试听课
            trial = Lesson.query.filter_by(student_id=current_user.id,lesson_type='Trial').order_by(Lesson.time.desc()).first()
            if trial:
                if trial.status == 'Complete' or trial.status == 'Not started':
                    return jsonify({'status':'fail','msg':"Operation failed.You've already booked a trial lesson."})
            time = time.split('-')
            #先构造一个没有时区的datetime对象
            time = datetime(int(time[0]),int(time[1]),int(time[2]),int(time[3]))
            #再把它变成时区为游客所在地区的datetime对象
            time = tz_obj.localize(time)
            #再把时区变成utc时区
            time = time.astimezone(utc)
            #再把课程信息存进数据库
            # 先看看学生之前是否已经选过同一时间同一老师的试听课了
            lesson = current_user.lessons.filter(Lesson.time==time,Lesson.teacher_id==teacher.id).first()
            if lesson:
                lesson.is_delete = False
            else:
                lesson = Lesson()
                lesson.student_id = current_user.id
                lesson.teacher_id = teacher.id
                lesson.time = time
                lesson.message = message
                lesson.lesson_type = 'Trial'
            db.session.add(lesson)
            return jsonify({'status':'ok','msg':"You've successfully booked a trial lesson."})
        return render_template('visitor/trial.html',
        this_week=this_week,
        new_worktime_list=new_worktime_list,
        only_dates=only_dates,
        month_name=month_name,
        year=year,
        current_page=current_page,
        teacher=teacher,
        lessons_list=lessons_list)
    
#游客所有课时包视图
@visitor.route('/my_packages')
@login_required
def my_packages():
    orders = current_user.orders.filter(Order.pay_status != 'canceled').order_by(Order.id.desc()).all()
    for order in orders:
        order.teacher = User.query.get(order.teacher_id)
    return render_template('visitor/my_packages.html',orders=orders)