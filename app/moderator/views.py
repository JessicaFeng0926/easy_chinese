from . import moderator

from flask import url_for,render_template,redirect,request,flash,jsonify
from flask_login import current_user,login_required
from flask_sqlalchemy import Pagination
from .. models import User,Order,Lesson
from .forms import AssignTeacherForm,ChangeTeacherForm,PreBookLessonForm
from app import db
from tools.ectimezones import get_localtime
from datetime import datetime,timedelta
from pytz import country_timezones,timezone
import calendar
from calendar import monthrange,monthcalendar,Calendar

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
            student_country=student.timezone
            if len(student_country)>2:
                student.timezone_str = country_timezones[student_country[:2]][int(student_country[-1])]
            else:
                student.timezone_str = country_timezones[student_country][0]
            
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

# 帮助学生选课的预处理视图，提交要选课的学生和老师
@moderator.route('/pre_book_lesson',methods=['GET','POST'])
@login_required
def pre_book_lesson():
    '''这是选课的预处理视图'''
    form = PreBookLessonForm()
    if form.validate_on_submit():
        student_username = form.student.data
        teacher_username = form.teacher.data
        return redirect(url_for('moderator.book_lesson',student_username=student_username,teacher_username=teacher_username))
    return render_template('moderator/pre_book_lesson.html',form=form)

# 选课视图
@moderator.route('/book_lesson/<student_username>/<teacher_username>',methods=['GET','POST'])
@login_required
def book_lesson(student_username,teacher_username):
    teacher = User.query.filter_by(username=teacher_username,role_id=3,is_delete=False).first()
    student = User.query.filter(User.username==student_username,User.is_delete==False).first()
    if teacher and (student.role_id==1 or student.role_id==2):
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

        #计算出协管员的时区
        visitor_country=current_user.timezone
        if len(visitor_country)>2:
            visitor_tz = country_timezones[visitor_country[:2]][int(visitor_country[-1])]
        else:
            visitor_tz = country_timezones[visitor_country][0]
        tz_obj = timezone(visitor_tz)

        # 根据时区，生成协管员视角的可以选课的28天的日历
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

        #把老师的可选的时间列表换成协管员时区的时间(字符串)
        for i,time in enumerate(new_worktime_list):
            time=time.astimezone(tz_obj)
            new_worktime_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        #把老师有课的时间转换成协管员时区的时间（字符串）
        for i,time in enumerate(lessons_list):
            time=time.astimezone(tz_obj)
            lessons_list[i]='%s-%s-%s-%s'%(time.year,time.month,time.day,time.hour)
        
        # 处理ajax请求
        time = request.args.get('time','',type=str)
        if time:
            time = time.split('-')
            #先构造一个没有时区的datetime对象
            time = datetime(int(time[0]),int(time[1]),int(time[2]),int(time[3]))
            #再把它变成时区为协管员所在地区的datetime对象
            time = tz_obj.localize(time)
            #再把时区变成utc时区
            time = time.astimezone(utc)

            # 再判断一次是否在可选时间范围内
            if time>=available_start:
                # 如果该用户是学生，需要操作课时包里的剩余课时
                if student.role_id == 2:
                    active_package = student.orders.filter(Order.pay_status=='paid',Order.left_amount>0).order_by(Order.pay_time.asc()).first()
                    if active_package:
                        # 课时包的课程数量扣掉一节
                        active_package.left_amount -= 1
                        db.session.add(active_package)
                        # 把选课信息存进数据库
                        lesson = student.lessons.filter(Lesson.time==time,Lesson.teacher_id==teacher.id).first()
                        if lesson:
                            lesson.is_delete = False
                        else:
                            lesson = Lesson()
                            lesson.student_id = student.id
                            lesson.teacher_id = teacher.id
                            lesson.time = time
                            lesson.message = ''
                            lesson.lesson_type =active_package.lesson_type
                        db.session.add(lesson)
                        msg = "您已经成功地为学生%s选了一节%s老师的%s课"%(student.username,teacher.name,active_package.lesson_type)
                        return jsonify({'status':'ok','msg':msg})
                    else:
                        return jsonify({'status':'ok','msg':'该生已经没有剩余课时，请联系该生购买课时包'})
                # 如果该用户是游客，需要查看是否已经上过试听课
                elif student.role_id == 1:
                    #如果该游客已经有一节试听课记录了，并且那节试听课是完成或者还未开始的状态，不允许他再次选择试听课
                    trial = Lesson.query.filter_by(student_id=student.id,lesson_type='Trial').order_by(Lesson.time.desc()).first()
                    if trial and (trial.status == 'Complete' or trial.status == 'Not started'):
                        return jsonify({'status':'fail','msg':"该生已经正常完成一节试听课，或正在等待一节试听课开始，不能再选"})
                    else:
                        # 先看看学生之前是否已经选过同一时间同一老师的试听课了
                        lesson = student.lessons.filter(Lesson.time==time,Lesson.teacher_id==teacher.id).first()
                        if lesson:
                            lesson.is_delete = False
                        else:
                            lesson = Lesson()
                            lesson.student_id = student.id
                            lesson.teacher_id = teacher.id
                            lesson.time = time
                            lesson.message = ''
                            lesson.lesson_type = 'Trial'
                        db.session.add(lesson)
                        msg = "您已经成功为学生%s选了一节%s老师的试听课"%(student.username,teacher.username)
                        return jsonify({'status':'ok','msg':msg})
            else:
                return jsonify({'status':'fail','msg':'您需要至少提前24小时选课'})
        return render_template('moderator/book_lesson.html',
        student=student,
        teacher=teacher,
        this_week=this_week,
        only_dates=only_dates,
        new_worktime_list=new_worktime_list,
        month_name=month_name,
        year=year,
        current_page=current_page,
        lessons_list=lessons_list
        )
    
    else:
        flash('学生或老师有误')
        return redirect(url_for('moderator.pre_book_lesson'))