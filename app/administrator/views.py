from . import administrator

from flask import url_for,render_template,redirect,request,flash,jsonify
from flask_login import login_required,current_user
from .forms import PersonalInfoForm
from tools.ectimezones import get_localtime
from app import db


# 管理员的个人信息
@administrator.route('/personal_info',methods=['GET','POST'])
@login_required
def personal_info():
    '''管理员的个人信息'''
    form = PersonalInfoForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        user.name = form.name.data
        user.location = form.location.data
        user.timezone = form.timezone.data
        db.session.add(user)
        flash('成功修改个人信息')
        return redirect(url_for('administrator.personal_info'))
    form.email.data = current_user.email
    form.username.data = current_user.username
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.timezone.data = current_user.timezone
    local_member_since = get_localtime(current_user.member_since,current_user)
    form.member_since.data = local_member_since.strftime('%Y-%m-%d')
    return render_template('administrator/personal_info.html',form=form)
