from . import moderator

from flask import url_for,render_template,redirect,request,flash,jsonify
from flask_login import current_user,login_required
from flask_sqlalchemy import Pagination
from .. models import User,Order,Lesson,SpecialRest,MakeUpTime,WorkTime
from .forms import AssignTeacherForm,ChangeTeacherForm,PreBookLessonForm,ModifyPersonalInfoForm,PreModifyScheduleForm,RestTimeForm,MakeupTimeForm
from app import db
from tools.ectimezones import get_localtime,get_utctime
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
                # 开课十分钟前，课程是可以取消的
                if lesson.time>datetime.utcnow()+timedelta(0,600):
                    lesson.cancel = True
                else:
                    lesson.cancel = False
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
        temp = teacher.make_up_time.filter_by(expire=False).all()
        for data in temp:
            makeup_time = datetime(data.make_up_time.year,data.make_up_time.month,data.make_up_time.day,data.make_up_time.hour,tzinfo=utc)
            if makeup_time>=available_start:
                makeup_time_list.append(makeup_time)
            # 把已经过期的补班时间的expire字段修改为True
            else:
                data.expire = True
                db.session.add(data)
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


# 取消学生的已选课程
@moderator.route('/cancel')
@login_required
def cancel():
    '''取消学生的已选课程'''
    lesson_id = request.args.get("id",0,type=int)
    if lesson_id:
        lesson=Lesson.query.get_or_404(lesson_id)
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

# 修改游客、学生、老师个人信息的预处理视图，主要是生成名单
@moderator.route('/pre_modify_info')
@login_required
def pre_modify_info():
    visitors = User.query.filter_by(role_id=1,is_delete=False).order_by(User.username.asc()).all()
    all_visitors = []
    count = 0
    temp = []
    for visitor in visitors:
        temp.append(visitor)
        count += 1
        if count == 4:
            all_visitors.append(temp)
            temp = []
            count = 0
    if temp:
        all_visitors.append(temp)
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
    teachers = User.query.filter_by(role_id=3,is_delete=False).order_by(User.username.asc()).all()
    all_teachers = []
    count = 0
    temp = []
    for teacher in teachers:
        temp.append(teacher)
        count += 1
        if count == 4:
            all_teachers.append(temp)
            temp = []
            count = 0
    if temp:
        all_teachers.append(temp)

    return render_template('moderator/pre_modify_info.html',all_visitors=all_visitors,all_students=all_students,all_teachers=all_teachers)

# 修改游客、学生、老师的个人信息，主要修改四个数据：
# 姓名、角色、时区、是否已经被删除
@moderator.route('/modify_personal_info/<username>',methods=['GET','POST'])
@login_required
def modify_personal_info(username):
    user = User.query.filter_by(username=username,is_delete=False).first()
    if user and user.role_id in {1,2,3}:
        form = ModifyPersonalInfoForm()
        if form.validate_on_submit():
            user.name = form.name.data
            user.role_id = int(form.role_id.data)
            user.timezone = form.timezone.data
            user.is_delete = form.is_delete.data
            db.session.add(user)
            flash('信息修改成功')
            return redirect(url_for('main.personal_center'))
        form.username.data = user.username
        form.name.data = user.name
        form.role_id.data = str(user.role_id)
        form.timezone.data = user.timezone
        form.is_delete.data = False
        return render_template('moderator/modify_personal_info.html',form=form)
    flash('用户不存在')
    return redirect(url_for('main.personal_center'))


# 修改教师的工作时间的预处理视图
@moderator.route('/pre_modify_schedule',methods=['GET','POST'])
@login_required
def pre_modify_schedule():
    form = PreModifyScheduleForm()
    if form.validate_on_submit():
        return redirect(url_for('moderator.modify_schedule',username=form.teacher.data,time_type=form.time_type.data))
    return render_template('moderator/pre_modify_schedule.html',form=form)

# 修改教师的工作时间
@moderator.route('/modify_schedule/<username>/<time_type>',methods=['GET','POST'])
@login_required
def modify_schedule(username,time_type):
    '''根据协管员提交的教师用户名和要修改的时间类型来处理
    :参数 username:教师的用户名
    :参数 time_type:要修改的时间类型
    '''
    teacher = User.query.filter_by(username=username,is_delete=False).first()
    if teacher:
        # 设置临时休息时间
        if time_type == '1':
            form = RestTimeForm()
            if form.validate_on_submit():
                available_start = datetime.utcnow()+timedelta(1)
                if form.end.data<=form.start.data or form.start.data<available_start:
                    flash('起始时间或结束时间有误')
                    return redirect(url_for('moderator.modify_schedule',username=username,time_type=time_type))
                else:
                    # 保存到数据库里,假设开始时间是9点，结束时间是11点
                    # 那就要保存9点和10点这两个时间点
                    time = form.start.data
                    end = form.end.data
                    while time<end:
                        naive_utctime = get_utctime(time,current_user)
                        sr = SpecialRest.query.filter_by(rest_time=naive_utctime,teacher_id = teacher.id,type=form.rest_type.data).first()
                        if not sr:
                            sr = SpecialRest()
                            sr.rest_time = naive_utctime
                            sr.teacher_id = teacher.id
                            sr.type = form.rest_type.data
                        sr.expire = False
                        db.session.add(sr)
                        time = time+timedelta(seconds=3600)
                    flash('休息时间设置成功')
                    return redirect(url_for('main.personal_center'))
            form.teacher.data = teacher.name
            return render_template('moderator/modify_schedule.html',form=form,username=username,time_type=time_type)
        # 设置临时的补班时间
        elif time_type == '2':
            form = MakeupTimeForm()
            if form.validate_on_submit():
                available_start = datetime.utcnow()+timedelta(1)
                if form.end.data<=form.start.data or form.start.data<available_start:
                    flash('起始时间或结束时间有误')
                    return redirect(url_for('moderator.modify_schedule',username=username,time_type=time_type))
                else:
                    # 把数据保存到数据库里面
                    time = form.start.data
                    end = form.end.data
                    while time<end:
                        naive_utctime = get_utctime(time,current_user)
                        mt = MakeUpTime.query.filter_by(make_up_time=naive_utctime,teacher_id = teacher.id).first()
                        if not mt:
                            mt = MakeUpTime()
                            mt.make_up_time = naive_utctime
                            mt.teacher_id = teacher.id
                        mt.expire = False
                        db.session.add(mt)
                        time = time+timedelta(seconds=3600)
                    flash('补班时间设置成功')
                    return redirect(url_for('main.personal_center'))
            form.teacher.data = teacher.name
            return render_template('moderator/modify_schedule.html',form=form,username=username,time_type=time_type)
        # 修改老师的常规工作时间
        elif time_type == '3':
            # 查询这位老师的工作时间，它们是UTC时间，还要转化为协管员时区的时间
            worktime = teacher.work_time.first().work_time
            worktime_list = worktime.split(';')
            # 让每个星期从星期天开始
            cal = Calendar(6)
            # 随便获取一个完整的naive的星期的日期
            week = cal.monthdatescalendar(2020,2)[0]
            # 获取utc时区对象
            utc = timezone('UTC')
            # 获取协管员时区对象
            moderator_country=current_user.timezone
            if len(moderator_country)>2:
                moderator_tz = country_timezones[moderator_country[:2]][int(moderator_country[-1])]
            else:
                moderator_tz = country_timezones[moderator_country][0]
            tz_obj = timezone(moderator_tz)
            # 用来存放按照这个星期来看，用户视角的上课时间（年月日小时）
            temp = []
            for w in worktime_list:
                date = week[int(w[0])]
                time = datetime(date.year,date.month,date.day,int(w[2:]),tzinfo=utc)
                time = time.astimezone(tz_obj)
                temp.append(time)
            # datetime里的6代表星期天，也就是我定义的0，这里用一个字典来保存这种映射关系
            weekday_map = {6:0,0:1,1:2,2:3,3:4,4:5,5:6}
            # 清空worktime_list列表，用于存储用户视角的常规工作时间
            worktime_list = []
            for time in temp:
                # 依然要把每个工作时间点变成0-1的形式，存进列表
                worktime_list.append(str(weekday_map[time.weekday()])+'-'+str(time.hour))
            return render_template('moderator/modify_schedule.html',username=username,time_type=time_type,teacher=teacher,worktime_list=worktime_list)
        else:
            flash('修改时间类型有误')
            return redirect(url_for('main.personal_center'))
    flash('教师不存在')
    return redirect(url_for('main.personal_center'))

# 设置教师的常规工作时间
@moderator.route('/modify_worktime',methods=['GET','POST'])
@login_required
def modify_worktime():
    '''设置教师的常规工作时间'''
    new_worktime = request.form.get('new_worktime','',type=str)
    username = request.form.get('username','',type=str)
    teacher = User.query.filter_by(username=username,role_id=3,is_delete=False).first()
    if teacher:
        # 把工作时间字符串变成列表
        new_worktime_list = new_worktime.split(';')
        # 上面是协管员视角的时间，还要转化为UTC时间，才能存储
        # 让每个星期从星期天开始
        cal = Calendar(6)
        # 随便获取一个完整的naive的星期的日期
        week = cal.monthdatescalendar(2020,2)[0]
        # 获取utc时区对象
        utc = timezone('UTC')
        # 获取协管员时区对象
        moderator_country=current_user.timezone
        if len(moderator_country)>2:
            moderator_tz = country_timezones[moderator_country[:2]][int(moderator_country[-1])]
        else:
            moderator_tz = country_timezones[moderator_country][0]
        tz_obj = timezone(moderator_tz) 
        # 用来存放按照这个星期来看，UTC的上课时间（年月日小时）
        temp = []
        for w in new_worktime_list:
            date = week[int(w[0])]
            time = datetime(date.year,date.month,date.day,int(w[2:]))
            time = time.astimezone(tz_obj)
            time = time.astimezone(utc)
            temp.append(time)
        # datetime里的6代表星期天，也就是我定义的0，这里用一个字典来保存这种映射关系
        weekday_map = {6:0,0:1,1:2,2:3,3:4,4:5,5:6}
        # 清空worktime_list列表，用于存储UTC的常规工作时间
        new_worktime_list = []
        for time in temp:
            # 依然要把每个工作时间点变成0-1的形式，存进列表
            new_worktime_list.append(str(weekday_map[time.weekday()])+'-'+str(time.hour))
        new_worktime_list.sort()
        new_worktime = ';'.join(new_worktime_list)
        # 查询出worktime表中该老师对应的对象，把更新保存到数据库中
        # 如果老师还没有这个对象，那就新建
        work_time = teacher.work_time.first() or WorkTime()
        work_time.work_time = new_worktime
        work_time.teacher_id = teacher.id
        db.session.add(work_time)
        return jsonify({'msg':'已经成功设置了教师时间'})
    return jsonify({'msg':'信息有误，请重试'})
