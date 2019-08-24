from flask import render_template,request,current_app,url_for,flash,redirect
from flask_login import current_user,login_user,logout_user,login_required
from . import auth
from . forms import SignUpForm,LoginForm,ChangePasswordForm,ResetPasswordRequestForm,ResetPasswordForm,ResetEmailRequestForm
from ..models import User
from .. import db
from tools.email import send_email

#注册
@auth.route('/sign_up',methods=['GET','POST'])
def sign_up():
    '''这是注册的视图'''
    form=SignUpForm()
    if form.validate_on_submit():
        new_user=User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    timezone=form.timezone.data)
        db.session.add(new_user)
        db.session.commit()
        token=new_user.generate_confirm_token()
        send_email([form.email.data],'Confirm your account','email/confirm',user=new_user,token=token)
        flash('An confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))   
    return render_template('auth/sign_up.html',form=form)


#确认账号
@auth.route('/confirm/<token>')
def confirm(token):
    '''这是确认账户的视图'''
    result = User.confirm(token)
    if result[0]:
        flash('Account \"%s\" has been confirmed.'%result[1])
    else:
        flash('The token is wrong or out of time.')
    return redirect(url_for('auth.login'))

#登录
@auth.route('/login',methods=['GET','POST'])
def login():
    '''这是登录的视图'''
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            if user.confirmed:
                if user.verify_password(form.password.data):
                    login_user(user)
                    return redirect(request.args.get('next') or url_for('main.index'))
                else:
                    flash('Invalid password.')
            else:
                token=user.generate_confirm_token()
                send_email([user.email],'Confirm your account','email/confirm',user=user,token=token)
                flash("Please go to your email and confirm your account.")
        else:
            flash('Invalid email.')
    return render_template('auth/login.html',form=form)

#退出
@auth.route('/logout')
def logout():
    '''退出登录的视图'''
    logout_user()
    return redirect(url_for('main.index'))

#忘记密码
#请求重置密码
@auth.route('/reset_password_request',methods=['GET','POST'])
def reset_password_request():
    '''这是请求重置密码的视图'''
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            token=user.generate_reset_password_token()
            send_email([user.email],'Reset Password','email/reset_password',user=user,token=token)
            flash('Please check your email to reset your password.')
        else:
            flash('Your email is wrong.')
    return render_template('auth/reset_password_request.html',form=form)

#完成重置密码
@auth.route('/reset_password/<token>',methods=['GET','POST'])
def reset_password(token):
    '''这是重置密码的视图'''
    form=ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token,form.password.data):
            flash('Successfully reset your password.')
            return redirect(url_for('auth.login'))
        else:
            flash('The token is wrong or out of time.')
    return render_template('auth/reset_password.html',form=form)


#修改密码
@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    '''这是修改密码的视图，必须在登录的情况下操作'''
    form=ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            user=current_user._get_current_object()
            user.password=form.password.data
            db.session.add(user)
            flash('Your password has been changed.')
            return redirect(url_for('main.index'))
        else:
            flash('Your old password was wrong.')
    return render_template('auth/change_password.html',form=form)


#修改邮箱
#请求修改邮箱
@auth.route('/reset_email_request',methods=['GET','POST'])
@login_required
def reset_email_request():
    '''这是发起修改邮箱请求的视图'''
    form=ResetEmailRequestForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            token=current_user.generate_reset_email_token(new_email=form.email.data)
            send_email([form.email.data],'Reset email','email/reset_email',user=current_user,token=token)
            flash('Please check your email to complete reseting your email.') 
            return redirect(url_for('auth.reset_email_request'))
        else:
            flash('Your password is wrong.')
    return render_template('auth/reset_email_request.html',form=form)

#完成邮箱修改
@auth.route('/reset_email/<token>')
@login_required
def reset_email(token):
    '''这是重置邮箱的视图'''
    if current_user.reset_email(token):
        flash('Successfully reset your email.')
    else:
        flash('Your token is wrong or out of time.')
    return redirect(url_for('main.index'))

