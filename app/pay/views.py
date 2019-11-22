from flask import redirect,render_template,request,url_for
from flask_login import login_required,current_user
from app.models import User,Lesson,Order
from . import pay

#课程价格信息视图
@pay.route('/course_info')
@login_required
def course_info():
    '''
    这是供所有已登录用于浏览的课程价格信息视图
    '''
    return render_template("pay/courses.html")

#点击购买按钮后的处理视图
@pay.route('/buy/<lesson_type>/<int:lesson_amount>/<int:time_limit>/<int:price>')
@login_required
def buy(lesson_type,lesson_amount,time_limit,price):
    '''
    用户点击购买按钮后就用这个视图处理

    ：参数 lesson_type:课程类型
    ：参数 lesson_amount:课程数
    ：参数 time_limit:完成时间限制
    ：参数 price:应付价格
    '''
    #对于游客，查询最近的trial老师
    if current_user.role_id == 1:
        latest_trial = current_user.lessons.order_by(Lesson.time.desc()).first()
        if latest_trial:
            teacher = User.query.get(int(latest_trial.teacher_id))
        #如果没有定过课，教师一项就显示缺省，后期分配
        else:
            teacher =  None

    #对于在校生，就查询他最新课时包的老师
    elif current_user.role_id == 2:
        teacher_id = current_user.orders.order_by(Order.pay_time.desc()).first().teacher_id
        teacher = User.query.get(teacher_id)

    return render_template('pay/confirm_order.html',
    lesson_type=lesson_type,
    lesson_amount=lesson_amount,
    time_limit=time_limit,
    price=price,
    teacher=teacher)

