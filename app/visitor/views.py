from . import visitor
from flask import render_template,url_for,current_app,request,flash,redirect,jsonify
from flask_login import current_user,login_required
from . forms import PersonalInfoForm
import os
from .. import db
from ..models import User
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
        #把以星期为单位的老师工作时间转化为以UTC的年月日小时为单位的工作时间
        #第一步：构造出utc的此时此刻
        cal = Calendar(6)
        utc=timezone('UTC')
        utcnow = datetime.utcnow()
        utcnow = datetime(utcnow.year,utcnow.month,utcnow.day,utcnow.hour,tzinfo=utc)
        #第二步：计算出可以选课的起始时间，也就是utcnow的24小时后，和截止时间，也就是utcnow的29天后
        available_start = utcnow+timedelta(1)
        available_end = utcnow+timedelta(29)
        #第三步：找到起始日期所在的星期、结束日期所在的星期，并拼接处包含可以选课的28天的日期列表，列表里的每个元素是一个子列表，子列表是一个以周日开始的星期
        #找出开始日期所在的星期
        for i,week in enumerate(cal.monthdatescalendar(available_start.year,available_start.month)):
            if available_start.date() in week:
                start_index = i
                break

        all_available_dates = cal.monthdatescalendar(available_start.year,available_start.month)[start_index:]
        #找到结束日期所在的星期
        for i,week in enumerate(cal.monthdatescalendar(available_end.year,available_end.month)):
            if available_end.date() in week:
                end_index=i
                break
        for week in cal.monthdatescalendar(available_end.year,available_end.month)[:end_index+1]:
            if week not in all_available_dates:
                #这个列表就是包含可以选课的28天的日期列表（实际的日期对象一般大于28）
                all_available_dates.append(week)

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
        #第六步：把教师的补班时间加到列表里
        makeup_time_list=[]
        for data in teacher.make_up_time.all():
            makeup_time_list.append(datetime(data.make_up_time.year,data.make_up_time.month,data.make_up_time.day,data.make_up_time.hour,tzinfo=utc))
        new_worktime_list+=makeup_time_list
        
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

        for i,week in enumerate(cal.monthdatescalendar(visitor_start.year,visitor_start.month)):
            if visitor_start.date() in week:
                start_index = i
                break

        visitor_dates = cal.monthdatescalendar(visitor_start.year,visitor_start.month)[start_index:]

        for i,week in enumerate(cal.monthdatescalendar(visitor_end.year,visitor_end.month)):
            if visitor_end.date() in week:
                end_index = i
                break

        for week in cal.monthdatescalendar(visitor_end.year,visitor_end.month)[:end_index+1]:
            if week not in visitor_dates:
                #这就是包含游客能选课的28天的日期列表，时区是游客时区
                visitor_dates.append(week)
        page = request.args.get('page',1,type=int)
        #如果有用户恶意修改page的数值，使得page超过了我们能接收的范围，我们就是手动让它重新等于1
        if page > len(visitor_dates) or page<1:
            page = 1
        
        #只有最后一个星期才以截止日期的月份为月份名，前面的几个星期都以开始日期为准
        if page<len(visitor_dates):
            month_name = calendar.month_name[visitor_start.month]
            year = visitor_start.year
        else:
            month_name = calendar.month_name[visitor_end.month]
            year = visitor_end.year

        current_page=Pagination(visitor_dates,page,1,len(visitor_dates),visitor_dates[page-1])
        
        this_week=[]
        only_dates=[]
        for date in current_page.items:
            this_week.append('%s-%s-%s'%(date.year,date.month,date.day))
            only_dates.append(date.day)
        
        #把老师的工作时间列表换成游客时区的时间(字符串)
        for i,time in enumerate(new_worktime_list):
            time=time.astimezone(tz_obj)
            new_worktime_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        
    return render_template('visitor/trial.html',this_week=this_week,new_worktime_list=new_worktime_list,only_dates=only_dates,month_name=month_name,year=year,current_page=current_page)

