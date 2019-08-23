from app import mail
from flask_mail import Message
from flask import current_app,render_template
from threading import Thread

def send_async_mail(app,msg):
    '''
    这是异步发送邮件的函数

    :参数 app:当前活动的app
    :参数 msg:邮件里要发送的消息
    '''
    with app.app_context():
        mail.send(msg)


def send_email(to,subject,template,**kwargs):
    '''
    这是发邮件的函数

    :参数 to:收件人邮箱,需要一个列表
    :参数 subject:邮件主题
    :参数 template:邮件正文模板
    :参数 **kwargs:模板里需要用的一些参数
    '''
    #获取当前app的实体
    app=current_app._get_current_object()
    msg=Message(subject=app.config['EC_MAIL_SUBJECT_PREFIX']+subject,sender=app.config['EC_MAIL_SENDER'],recipients=to)
    msg.html=render_template(template+'.html',**kwargs)
    t=Thread(target=send_async_mail,args=(app,msg))
    t.start()
    return t