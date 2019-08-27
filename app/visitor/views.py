from . import visitor
from flask import render_template,url_for,current_app,request,flash,redirect,jsonify
from flask_login import current_user,login_required
from . forms import PersonalInfoForm
import os
from .. import db
from ..models import User
from pytz import country_timezones,timezone
from datetime import datetime
from calendar import monthcalendar


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
        #第一步：找出UTC的此时此刻的年月日
        utc = timezone('UTC')
        utc_today = datetime.today().astimezone(utc)
        utc_year = utc_today.year
        utc_month = utc_today.month
        utc_day = utc_today.day
        #第二步：找出UTC的本周（这是一个较长的星期，前后各扩展一天，这是为了防止游客的时间和老师相差一天）
        utc_month_calendar = monthcalendar(utc_year,utc_month)
        for i,week in enumerate(utc_month_calendar):
            if utc_day in week:
                utc_this_week = week
                break
        utc_this_week = utc_month_calendar[i-1][5:7]+utc_this_week
        #第三步：把本周列表里的每个元素都换成包含年月日的datetime对象，时区是UTC
        for i,date in enumerate(utc_this_week):
            if date !=0:
                utc_this_week[i]=datetime(utc_year,utc_month,date,tzinfo=utc)
        if utc_this_week[-1] == 0:
            zero_num = utc_this_week.count(0)
            utc_next_month = utc_month + 1
            if utc_month == 12:
                utc_next_month = 1
                utc_year = utc_year + 1
            for i in range(zero_num):
                utc_this_week[9-zero_num+i] = datetime(utc_year,utc_next_month,i+1,tzinfo=utc)

        #第四步：根据老师的工作时间，生成一个新的列表，列表里的每项都是包含年月日小时的datetime对象，时区是UTC
        new_worktime_list=[]
        for i in worktime_list:
            new_worktime_list.append(datetime(utc_this_week[int(i[0])+1].year,utc_this_week[int(i[0])+1].month,utc_this_week[int(i[0])+1].day,int(i[2:]),tzinfo=utc))
            if int(i[0]) == 6:
                new_worktime_list.append(datetime(utc_this_week[0].year,utc_this_week[0].month,utc_this_week[0].day,int(i[2:]),tzinfo=utc))
            elif int(i[0]) == 0:
                new_worktime_list.append(datetime(utc_this_week[-1].year,utc_this_week[-1].month,utc_this_week[-1].day,int(i[2:]),tzinfo=utc)) 


        #计算出游客的时区
        visitor_country=current_user.timezone
        if len(visitor_country)>2:
            visitor_tz = country_timezones[visitor_country[:2]][int(visitor_country[-1])]
        else:
            visitor_tz = country_timezones[visitor_country]
        tz_obj = timezone(visitor_tz)

        #根据时区，生成游客的本周日历
        #生成游客当地的当日日期
        visitor_today = datetime.today().astimezone(tz_obj)    
        visitor_year = visitor_today.year
        visitor_month = visitor_today.month
        visitor_day = visitor_today.day
        #游客的当月日历
        month_calendar = monthcalendar(visitor_year,visitor_month)
        for i,week in enumerate(month_calendar):
            if visitor_day in week:
                this_week = week
                break
        #拼接出游客的“当周”，以星期天作为第一天
        this_week=month_calendar[i-1][6:7]+this_week[:-1]
        only_dates=[]
        for i,date in enumerate(this_week):
            if date != 0:
                this_week[i] = "%s-%s-%s"%(visitor_year,visitor_month,date)
                only_dates.append(date)
        #如果当周末尾有0，就要把那些0替换成下个月的1,2,3……
        if this_week[-1] == 0:
            zero_num=this_week.count(0)
            next_month = visitor_month + 1
            if visitor_month == 12:
                next_month = 1
                visitor_year = visitor_year+1
            for i in range(zero_num):
                this_week[7-zero_num+i] == '%s-%s-%s'%(visitor_year,next_month,i+1)
                only_dates.append(i+1)
        #把老师的工作时间列表换成游客时区的时间(字符串)
        for i,time in enumerate(new_worktime_list):
            time=time.astimezone(tz_obj)
            new_worktime_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)

    return render_template('visitor/trial.html',this_week=this_week,new_worktime_list=new_worktime_list,only_dates=only_dates)

