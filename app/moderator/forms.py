from flask_wtf import FlaskForm
from wtforms.fields import StringField,SubmitField,SelectField,BooleanField,DateTimeField
from wtforms.validators import Required,Length,Email
from tools.teacher_list import teacher_list
from tools.visitor_student_list import visitor_student_list
from tools.ectimezones import ectimezone_list

class AssignTeacherForm(FlaskForm):
    '''这是给新生分配老师的表单类'''
    username = StringField(label='学生',render_kw={'readonly':True})
    old_teachers = StringField(label='未见面的试听课老师',render_kw={'readonly':True})
    primary_teacher = SelectField(label='主管老师',choices=teacher_list,validators=[Required()])
    submit = SubmitField(label='提交')


class ChangeTeacherForm(FlaskForm):
    '''这是给在校生更换老师的表单类'''
    username = StringField(label='学生',render_kw={'readonly':True},validators=[Required()])
    old_teachers = StringField(label='过去的老师',render_kw={'readonly':True})
    current_teacher = StringField(label='现任主管老师',render_kw={'readonly':True})
    new_teacher = SelectField(label='新主管老师',choices=teacher_list,validators=[Required()])
    submit = SubmitField(label='提交')


class PreBookLessonForm(FlaskForm):
    '''这是提交要选课的学生和老师的表单类'''
    student = SelectField(label='学生',choices=visitor_student_list,validators=[Required()])
    teacher = SelectField(label='老师',choices=teacher_list,validators=[Required()])
    submit = SubmitField(label='提交')

class ModifyPersonalInfoForm(FlaskForm):
    '''这是修改游客、学生和老师的信息的表单类'''
    username = StringField(label='用户名',render_kw={'readonly':True})
    name = StringField(label='姓名',validators=[Length(0,64)])
    role_id = SelectField(label='角色',choices=[['1','游客'],['2','学生'],['3','教师'],['4','协管员']])
    timezone = SelectField(label='时区',choices=ectimezone_list,validators=[Required()])
    is_delete = BooleanField(label='已删除',false_values=('False',))
    submit = SubmitField(label='提交')


class PreModifyScheduleForm(FlaskForm):
    '''这是修改教师工作时间的预处理视图'''
    teacher = SelectField(label='教师',choices=teacher_list)
    time_type = SelectField(label='时间类型',choices=[['1','临时休息'],['2','补班'],['3','修改常规工作时间'],['4','取消休息'],['5','取消补班']])
    submit = SubmitField(label='提交')


class RestTimeForm(FlaskForm):
    '''这是临时休息时间表单'''
    teacher = StringField(label='教师',render_kw={'readonly':True})
    rest_type = SelectField(label='休息类型',choices=[['off','请假'],['meet','会议'],['lieu','调休']])
    start = DateTimeField(label='起始时间',validators=[Required()],description='格式:2008-8-18 8:00:00,请以你自己所在时区为准')
    end = DateTimeField(label='结束时间',validators=[Required()],description='格式:2008-8-18 9:00:00,请你以自己所在时区为准')
    submit = SubmitField(label='提交')

class MakeupTimeForm(FlaskForm):
    '''这是补班时间表单'''
    teacher = StringField(label='教师',render_kw={'readonly':True})
    start = DateTimeField(label='起始时间',validators=[Required()],description='格式:2008-8-18 8:00:00,请以你自己所在时区为准')
    end = DateTimeField(label='结束时间',validators=[Required()],description='格式:2008-8-18 8:00:00,请以你自己所在时区为准')
    submit = SubmitField(label='提交')

class PersonalInfoForm(FlaskForm):
    '''个人信息'''
    name=StringField(label='Your real name',validators=[Required(),Length(1,64)])
    location=StringField(label='Location',validators=[Length(0,64)],render_kw={'placeholder':'i.e. New York,US'})
    timezone=SelectField(label='Timezone',validators=[Required()],choices=ectimezone_list,description='Timezone is very important to booking lessons,please be careful.')
    username=StringField(label='Username',render_kw={'readonly':True},validators=[Required()])
    email=StringField(label='Email',validators=[Required(),Email()],render_kw={'readonly':True})
    member_since=StringField(label='Member since',validators=[Required()],render_kw={'readonly':True})
    submit=SubmitField(label='Submit')