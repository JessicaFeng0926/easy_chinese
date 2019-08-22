from flask import render_template,request,current_app,url_for,flash,redirect
from flask_login import current_user
from . import auth
from . forms import SignUpForm,LoginForm
from ..models import User
from .. import db

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
        flash('Successfully signed up.Welcome to Easy Chinese.')
        return redirect(url_for('main.index'))   
    return render_template('auth/sign_up.html',form=form)

@auth.route('/login',methods=['GET','POST'])
def login():
    '''这是登录的视图'''
    form = LoginForm()
    if form.validate_on_submit():
        pass
    return render_template('auth/login.html',form=form)
    