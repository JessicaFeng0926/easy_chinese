from flask_wtf import FlaskForm
from wtforms.fields import StringField,SubmitField,SelectField,BooleanField
from wtforms.validators import Required,Length
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