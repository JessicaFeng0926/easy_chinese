from flask import current_app,url_for,render_template,redirect,flash,request
from flask_login import current_user,login_required
from . import student
from .forms import PersonalInfoForm
from ..models import User
import os
from ..import db


#个人信息
@student.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''这是学生的个人信息视图'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user=current_user._get_current_object()
        user.name = form.name.data
        user.location = form.location.data
        user.timezone = form.timezone.data
        if 'image' in request.files:
            file = request.files['image']
            if file:
                cleaned_filename=User.validate_image(file.filename)
                UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
                file.save(os.path.join(UPLOAD_FOLDER,cleaned_filename))
                user.image = cleaned_filename
        db.session.add(user)
        flash('Successfully modified your personal information')
        return redirect(url_for('student.personal_info'))

    form.image.data = current_user.image
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.member_since.data = current_user.member_since.strftime('%Y-%m-%d')
    return render_template('student/personal_info.html',form=form)




