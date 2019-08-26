from . import visitor
from flask import render_template,url_for,current_app,request,flash,redirect,jsonify
from flask_login import current_user,login_required
from . forms import PersonalInfoForm
import os
from .. import db
from ..models import User


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
    sid = request.form.get('sid',0,type=int)
    if sid :
        result = sid + 1
        return jsonify({'status':'ok','msg':result})
    return render_template('visitor/trial.html')

