from flask_wtf import FlaskForm
from wtforms.fields import StringField,SelectField,SubmitField,FileField
from wtforms.validators import Required,Email,Length
from wtforms.widgets import TextArea
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

class EditProfileForm(FlaskForm):
    '''这是主管学生信息的表单'''
    nickname = StringField(label='称呼',validators=[Length(1,64)],render_kw={'placeholder':'学生喜欢的称呼，如Michael,陈先生等。如果发音比较特殊，也请标注。'})
    gender = StringField(label='性别',validators=[Length(1,32)])
    age = StringField(label='年龄',validators=[Length(1,32)])
    job = StringField(label='工作情况',validators=[Length(1,128)])
    family = StringField(label='家庭情况',validators=[Length(1,128)])
    personality = StringField(label='性格特点',validators=[Length(1,128)])
    hobby = StringField(label='兴趣爱好',validators=[Length(1,128)])
    taboo = StringField(label='禁忌话题',validators=[Length(1,128)],render_kw={'placeholder':'如学生比较敏感的宗教问题，去世的亲人或离异的父母、伴侣等。'})
    reason = StringField(label='学习原因',validators=[Length(1,128)])
    goal = StringField(label='学习目标',validators=[Length(1,128)],render_kw={'placeholder':'请尽量覆盖听说读写等多个方面'})
    level = StringField(label='当前水平',validators=[Length(1,128)],render_kw={'placeholder':'请尽量覆盖听说读写等多个方面'})
    ability = StringField(label='学习能力',validators=[Length(1,128)])
    notes = StringField(label='是否需要笔记或录音',validators=[Length(1,128)])
    homework = StringField(label='是否需要作业',validators=[Length(1,128)])
    teacher_phone = StringField(label='主管老师电话',validators=[Length(1,128)])
    submit = SubmitField(label='修改并提交')

class RecordLessonForm(FlaskForm):
    '''这是记录课程详情的表单类'''
    talk = StringField(label='寒暄',validators=[Length(1,256)],widget=TextArea())
    this_lesson = StringField(label='这节课学了什么',validators=[Length(1,256)],widget=TextArea())
    next_lesson = StringField(label='下节课安排',validators=[Length(1,256)],widget=TextArea())
    homework = StringField(label='作业',validators=[Length(1,256)],widget=TextArea())
    textbook = StringField(label='教材',validators=[Length(1,256)],render_kw={'placeholder':'请写清楚教材名称、版本以及册数，如《新实用汉语课本》第2版第一册'},widget=TextArea())
    other = StringField(label='其他注意事项',validators=[Length(1,256)],widget=TextArea())
    status = SelectField(label='课时完成状态',validators=[Required()],choices=[['Complete','正常完成'],['Stu Absent','学生缺勤'],['Tea Absent','教师缺勤'],['Tea Late','教师迟到']])
    submit = SubmitField(label='提交')