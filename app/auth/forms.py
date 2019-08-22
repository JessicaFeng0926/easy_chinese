from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SelectField,SubmitField
from wtforms.validators import Email,Required,Length,EqualTo,Regexp
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


