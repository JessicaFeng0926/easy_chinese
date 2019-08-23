from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SelectField,SubmitField
from wtforms.validators import Email,Required,Length,EqualTo,Regexp
from wtforms.widgets import Input,html_params
from ..models import User
from wtforms import ValidationError
from tools.ectimezones import ectimezone_list

class SignUpForm(FlaskForm):
    '''这是注册表单类'''
    email=StringField(label='Email',validators=[Required(),Length(1,64),Email()])
    username=StringField(label='Username',validators=[Required(),Length(1,64),Regexp(regex='^[A-Za-z][A-Za-z._]*$',flags=0,message='The username can only contains letters,numbers ,dot and underscore.')])
    password=PasswordField(label='Password',validators=[Required(),Length(1,128),EqualTo('password2',message='The two passwords should be the same.')])
    password2=PasswordField(label='Password Again',validators=[Required(),Length(1,128)])
    timezone=SelectField(label='What is your timezone?',validators=[Required()],choices=ectimezone_list)
    submit=SubmitField(label='Sign up')

    def validate_email(self,field):
        '''这是对邮箱的进一步验证，保证不能用被占用的邮箱'''
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email has been used.')
    
    def validate_username(self,field):
        '''这是对用户名的进一步验证，确保用户名的唯一性'''
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('This username has been used.')

class LoginForm(FlaskForm):
    '''这是登录的表单类'''
    email=StringField(label='Email',validators=[Required(),Length(1,64),Email()])
    password=PasswordField(label='Password',validators=[Required(),Length(1,128)])
    submit=SubmitField(label='Log in')

class ChangePasswordForm(FlaskForm):
    '''这是修改密码的表单类'''
    old_password=PasswordField(label='Your old password',validators=[Required(),Length(1,128)],render_kw={'placeholder':'Enter your password'})
    password=PasswordField(label='Your new password',validators=[Required(),Length(1,128),EqualTo('password2',message='Two new passwords should be the same.')],render_kw={'placeholder':'Password should be less than 128 characters'})
    password2=PasswordField(label='Confirm your new password',validators=[Required()],render_kw={'placeholder':'Please be careful,this password should be the same as the above one.'})
    submit=SubmitField(label='Change')

class ResetPasswordRequestForm(FlaskForm):
    '''这是请求重置密码的表单类'''
    email=StringField(label='Email',validators=[Required(),Email()],render_kw={'placeholder':'Please enter the email which is used to log in our website'})
    submit=SubmitField(label='Submit')

class ResetPasswordForm(FlaskForm):
    '''这是完成重置密码的表单类'''
    password=PasswordField(label='New password',validators=[Required(),Length(1,128),EqualTo('password2',message='Two passwords shold be the same.')])
    password2=PasswordField(label='Confirm your new password',validators=[Required()])
    submit=SubmitField(label='Submit')

class ResetEmailRequestForm(FlaskForm):
    '''这是请求修改邮箱的表单类'''
    email=StringField(label='New email',validators=[Required(),Length(1,64),Email()])
    password=PasswordField(label='Password',validators=[Required(),Length(1,128)])
    submit=SubmitField(label='Submit')

    def validate_email(self,field):
        '''对新邮箱的进一步验证，不能被别人占用了'''
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email has been used.')
