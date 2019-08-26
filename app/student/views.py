from flask import current_app,url_for,render_template,redirect
from flask_login import current_user,login_required
from . import student
from .forms import PersonalInfoForm


#个人信息
@student.route('/personal_info')
@login_required
def personal_info():
    '''这是学生的个人信息视图'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        pass
    form.image.data = current_user.image
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.member_since.data = current_user.member_since.strftime('%Y-%m-%d')
    return render_template('student/personal_info.html',form=form)




