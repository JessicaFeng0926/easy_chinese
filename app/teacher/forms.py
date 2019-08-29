from flask_wtf import FlaskForm
from wtforms.fields import StringField,SelectField,SubmitField,FileField
from wtforms.validators import Required,Email,Length
from tools.ectimezones import ectimezone_list

class PersonalInfoForm(FlaskForm):
    '''这是教师个人信息的表单'''
    image=FileField(label='Image',validators=[Required()])
    name=StringField(label='Your real name',validators=[Required(),Length(1,64)])
    location=StringField(label='Location',validators=[Length(0,64)],render_kw={'placeholder':'i.e. New York,US'})
    timezone=SelectField(label='Timezone',validators=[Required()],choices=ectimezone_list,description='Timezone is very important to booking lessons,please be careful.')
    username=StringField(label='Username',render_kw={'readonly':True},validators=[Required()])
    email=StringField(label='Email',validators=[Required(),Email()],render_kw={'readonly':True})
    member_since=StringField(label='Member since',validators=[Required()],render_kw={'readonly':True})
    submit=SubmitField(label='Submit')
