from flask import redirect,render_template,request,url_for,jsonify
from flask_login import login_required,current_user
from app.models import User,Lesson,Order,StudentProfile
from . import pay
from app import db
from alipay import AliPay
import os
from config import basedir
from tools.exrate import dollar_2_rmb
from datetime import datetime,timedelta

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

#提交订单后的处理视图
@pay.route('/submit_order/<lesson_type>/<int:lesson_amount>/<int:time_limit>/<int:price>/<teacher_id>')
@login_required
def submit_order(lesson_type,lesson_amount,time_limit,price,teacher_id):
    '''
    这是提交订单后的创建新订单并存进数据库的视图

    :参数 lesson_type:课程类型
    :参数 lesson_amount:课时数
    :参数 time_limit:完成课时的时间限制
    :参数 price:课时包的价格
    :参数 teacher_id:教师id
    '''

    order = Order()
    order.lesson_type = lesson_type
    order.lesson_amount = lesson_amount
    order.time_limit = time_limit
    order.student_id = current_user.id
    order.left_amount = lesson_amount
    order.price = price
    order.pay_status = 'waiting'
    if teacher_id!='None':
        order.teacher_id = teacher_id
    #对于游客而言，那些没有正常完成的FT课老师，也算是他的past teachers
    #因为学生可能会对这些老师印象不好
    if current_user.role_id == 1:
        #查询该游客的所有试听课，按时间降序排列
        trials = current_user.lessons.order_by(Lesson.time.desc()).all()
        #如果确实订过试听课
        if trials:
            #把所有试听课的老师id存进一个列表
            teachers_id_list = [trial.teacher_id for trial in trials]
            #如果这个列表长度大于1，说明跟不止一位老师打过交道，继续下面的步骤
            if len(teachers_id_list)>1:
                #先把第1位老师的id存进字符串（第0位老师是现任老师，不是过去的老师）
                past_id_str = str(teachers_id_list[1])
                #再把后面所有的老师都拼接进字符串
                for past_id in teachers_id_list[2:]:
                    past_id_str = past_id_str+';'+str(past_id)
                #把这个大字符串存进这个订单的过去老师字段
                order.past_teachers = past_id_str
    db.session.add(order)
    if current_user.role_id == 1:
        return redirect(url_for('visitor.my_packages'))
    return redirect(url_for('student.my_packages'))

#这是支付的视图
@pay.route('/pay_order')
@login_required
def pay_order():
    '''
    这是支付订单的视图
    :参数 order_id:订单号
    '''
    #查找符合条件的订单
    order_id = request.args.get('order_id',0,type=int)
    order = Order.query.filter(Order.id==order_id,Order.student_id==current_user.id,Order.pay_status=='waiting').first()
    if order:
        #获取app私钥
        app_private_key_string = open(os.path.join(basedir,'tools/app_private_key.pem')).read()
        #获取支付宝公钥
        alipay_public_key_string = open(os.path.join(basedir,'tools/alipay_public_key.pem')).read()
        #创建支付宝sdk的工具对象
        alipay_client = AliPay(
            appid="2016101700704120", #这是从沙箱里拿过来的
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2", # RSA 或者 RSA2
            debug=True  # 默认False,我们是沙箱环境，所以变成True
        )

        #提交订单数据(支付成功后跳转到修改数据库中订单状态的视图)
        
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id, #订单编号
            total_amount=str(dollar_2_rmb(order.price)), #金额以元为单位
            subject='Easy Chinese %s'%order_id,
            return_url="http://127.0.0.1:5000/pay/pay_complete/"+str(order_id),
            notify_url=None # 可选, 不填则使用默认notify url
            )

        #构建让支付宝跳转的链接地址
        pay_url = "https://openapi.alipaydev.com/gateway.do?"+order_string
        
        return jsonify({'status':'ok','msg':pay_url})
    else:
        return jsonify({'status':'fail','msg':'Order information error'})
     
#支付完成后修改订单数据的视图
@pay.route('/pay_complete/<int:order_id>')
@login_required
def pay_complete(order_id):
    '''修改订单状态'''
    order = Order.query.filter(Order.id==order_id,Order.student_id==current_user.id).first()
    if order:
        order.pay_status='paid'
        order.pay_time = datetime.utcnow()
        order.end_time = datetime.utcnow()+timedelta(order.time_limit*30)
        db.session.add(order)
        if current_user.role_id == 1:
            current_user.role_id = 2
            db.session.add(current_user)
            # 给这个学生创建简历
            new_profile = StudentProfile()
            new_profile.student_id=current_user.id
            # 如果订单里面有老师，就建立师生关系，没有就先空着
            # 协管员会给学生分配老师的。
            if order.teacher_id:
                new_profile.teacher_id = order.teacher_id
            db.session.add(new_profile)
        return redirect(url_for('student.my_packages'))
    else:
        flash('Order information error')
        return redirect(url_for('main.index'))

    

