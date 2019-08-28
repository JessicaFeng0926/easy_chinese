from . import visitor
from flask import render_template,url_for,current_app,request,flash,redirect,jsonify
from flask_login import current_user,login_required
from . forms import PersonalInfoForm
import os
from .. import db
from ..models import User
from pytz import country_timezones,timezone
from datetime import datetime,timedelta
from calendar import monthcalendar,monthrange


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
        return redirect(url_for('visitor.personal_info',username=current_user.username))


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
        #第一步：找出UTC的此时此刻
        utc=timezone('UTC')
        utcnow = datetime.utcnow()
        utcnow=datetime(utcnow.year,utcnow.month,utcnow.day,utcnow.hour,utcnow.minute,utcnow.second,utcnow.microsecond,tzinfo=utc)
        #第二步：计算出可以选课的起始时间，也就是utcnow的24小时后，和截止时间，也就是utcnow的29天后
        available_start = utcnow + timedelta(1)
        available_end = utcnow + timedelta(29)
        #第三步：找出可以选课的起始日期和截止日期是星期几
        available_start_weekday = available_start.weekday()
        available_end_weekday = available_end.weekday()
        #第四步：找出可以选课的起始时期和截止日期所在的月份的最大日期
        start_monthrange=monthrange(available_start.year,available_start.month)[1]
        end_monthrange=monthrange(available_end.year,available_end.month)[1]
        #第五步：构造出可以选课的28天的日期列表，元素是datetime对象，时区是UTC

        available_time_list=[]
        if available_start.month == available_end.month:
            for i in range(29):
                available_time_list.append(datetime(available_start.year,available_start.month,available_start.day+i,tzinfo=utc))
        elif available_start.month+1 == available_end.month or available_start.year+1 == available_end.year+1:
            for i in range(start_monthrange-available_start.day+1):
                available_time_list.append(datetime(available_start.year,available_start.month,available_start.day+i,tzinfo=utc))
            for i in range(29-(start_monthrange-available_start.day+1)):
                available_time_list.append(datetime(available_end.year,available_end.month,i+1,tzinfo=utc))    
        #第六步：把刚才得到的长列表分成4个或5个星期，不足一星期的就补零处理，然后把列表里的每个元素都根据教师的工作时间变成精确到小时的datetime对象，UTC时区
        new_worktime_list=[]
        if available_start_weekday == 6:
            for i in range(4):
                for w in worktime_list:
                    date=available_time_list[7*i:7*i+7][int(w[0])]
                    time= datetime(date.year,date.month,date.day,int(w[2:]),tzinfo=utc)
                    #如果这个时间早于允许选课的开始时间或者大于允许选课的截止时间，就不添加到列表里
                    if time<available_start or time>available_end:
                        continue
                    new_worktime_list.append(time)
        else:
            #前后补零，总共补的0的个数是7
            available_time_list=[0]*(available_start_weekday+1)+available_time_list+[0]*(7-available_start_weekday-1)
            for i in range(5):
                for w in worktime_list:
                    date=available_time_list[7*i:7*i+7][int(w[0])]
                    #如果取出来的不是日期对象，而是我们补的0，就跳过
                    if date == 0:
                        continue
                    time = datetime(date.year,date.month,date.day,int(w[2:]),tzinfo=utc)
                    if time<available_start or time>available_end:
                        continue
                    new_worktime_list.append(time)
        #第七步：把教师的特殊休息时间从列表中去除
        special_rest_list = []
        for data in teacher.special_rest.all():
            special_rest_list.append(datetime(data.rest_time.year,data.rest_time.month,data.rest_time.day,data.rest_time.hour,tzinfo=utc))
        for i in new_worktime_list[:]:
            if i in special_rest_list:
                new_worktime_list.remove(i)
        #第八步：把教师的补班时间加到列表里
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
        
        #根据时区，生成游客的本周日历（本周的含义是包含选课的起始时间的那一周）
        #生成游客当地的当日日期
        visitor_start = datetime(available_start.year,available_start.month,available_start.day,tzinfo=tz_obj)
        #游客的当月日历 
        month_calendar = monthcalendar(visitor_start.year,visitor_start.month)
        for i,week in enumerate(month_calendar):
            if visitor_start.day in week:
                this_week = week
                break
        #拼接出游客的“当周”，以星期天作为第一天
        this_week=month_calendar[i-1][6:7]+this_week[:-1]
        only_dates=[]
        for i,date in enumerate(this_week):
            if date != 0:
                this_week[i] = "%s-%s-%s"%(visitor_start.year,visitor_start.month,date)
                only_dates.append(date)
        #如果当周末尾有0，就要把那些0替换成下个月的1,2,3……
        if this_week[-1] == 0:
            zero_num=this_week.count(0)
            next_month = visitor_start.month + 1
            visitor_year = visitor_start.year
            if visitor_start.month == 12:
                next_month = 1
                visitor_year = visitor_start.year+1
            for i in range(zero_num):
                this_week[7-zero_num+i] = '%s-%s-%s'%(visitor_year,next_month,i+1)
                only_dates.append(i+1)
        #如果当周的开头有0，就要把那些0替换成上个月的最后几个日期
        if this_week[0] == 0:
            zero_num=this_week.count(0)
            last_month=visitor_start.month -1
            visitor_year = visitor_start.year
            if visitor_start.month == 1:
                last_month = 12
                visitor_year = visitor_start.year-1
            last_month_range=monthrange(visitor_year,last_month)[1]
            for i in range(zero_num):
                this_week[i] = '%s-%s-%s-%s'%(visitor_year,last_month,last_month_range-zero_num+i+1)
                only_dates.insert(i,last_month_range-zero_num+i+1)
        #把老师的工作时间列表换成游客时区的时间(字符串)
        for i,time in enumerate(new_worktime_list):
            time=time.astimezone(tz_obj)
            new_worktime_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        
    return render_template('visitor/trial.html',this_week=this_week,new_worktime_list=new_worktime_list,only_dates=only_dates)

