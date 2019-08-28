from . import db,login_manager
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from werkzeug.utils import secure_filename
import random
from wtforms import ValidationError

class Role(db.Model):
    '''这是用户角色的模型类'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    #角色名字
    name = db.Column(db.String(64),unique=True,index=True)
    #是否是默认角色
    default = db.Column(db.Boolean,default=False,index=True)
    #权限
    permissions=db.Column(db.Integer)
    #声明一对多关系
    users = db.relationship('User',backref='role',lazy='dynamic')
    
    @staticmethod
    def insert_roles():
        '''这是向数据库里插入所有角色的方法'''
        roles={
            'Visitor':(Permission.BOOK_TRIAL,True),
            'Student':(Permission.BOOK_LESSON,False),
            'Teacher':(Permission.RECORD_LESSON_DETAIL | 
                       Permission.MANAGE_STUDENT_PROFILE,False),
            'Moderator':(Permission.BOOK_TRIAL_FOR_OTHERS | 
                        Permission.BOOK_LESSON_FOR_OTHERS | 
                        Permission.MODIFY_TIMETABLE | 
                        Permission.MANAGE_RELATIONSHIP|
                        Permission.MODIFY_INFO_FOR_OTHERS |
                        Permission.RESET_PASSWORD_FOR_OTHERS,False),
            'Administrator':(Permission.ADMINISTRATOR,False)
        }
        for k,v in roles.items():
            if Role.query.filter_by(name=k).first():
                continue
            r=Role(name=k,permissions=v[0],default=v[1])
            db.session.add(r)
        db.session.commit()


    def __repr__(self):
        '''返回字符串描述'''
        return '<Role %s>'%self.name

class Permission():
    '''权限常量类'''
    #给自己选试听课，[游客，管理员]
    BOOK_TRIAL = 0x0001
    #给自己选常规课，[学生，管理员]
    BOOK_LESSON = 0x0002
    #给别人选试听课，[协管员，管理员]
    BOOK_TRIAL_FOR_OTHERS = 0x0004
    #给别人选常规课，[协管员，管理员]
    BOOK_LESSON_FOR_OTHERS = 0x0008
    #修改休息教师的时间，[协管员，管理员]
    MODIFY_TIMETABLE = 0x0010
    #建立或修改师生关系,[协管员，管理员]
    MANAGE_RELATIONSHIP = 0x0020
    #修改他人的资料,[协管员，管理员]
    MODIFY_INFO_FOR_OTHERS = 0x0040
    #填写课程完成情况，[老师，管理员]
    RECORD_LESSON_DETAIL = 0x0080
    #填写学生的学习档案,[老师，管理员]
    MANAGE_STUDENT_PROFILE = 0x0100
    #修改他人的密码,[协管员，管理员]
    RESET_PASSWORD_FOR_OTHERS = 0x0200
    #管理员权限，这是全面所有权限之和
    ADMINISTRATOR = 0x03ff




class User(UserMixin,db.Model):
    '''这是用户的模型类，继承自Model类和UserMixin类'''
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key = True)
    #邮箱
    email = db.Column(db.String(64),unique=True,index=True)
    #用户名
    username = db.Column(db.String(64),unique=True,index=True)
    #密码的哈希值
    password_hash = db.Column(db.String(128))
    #时区
    timezone = db.Column(db.String(8))
    #是否确认
    confirmed = db.Column(db.Boolean,default=False)
    #姓名
    name = db.Column(db.String(64))
    #位置
    location = db.Column(db.String(64))
    #加入本站的时间
    member_since = db.Column(db.DateTime,default=datetime.utcnow)
    #最后一次上课的时间
    last_seen = db.Column(db.DateTime)
    #头像路径
    image = db.Column(db.String(128),unique=True)
    #绑定外键，用户角色
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
    #声明和工作时间表的一对一关系
    work_time = db.relationship('WorkTime',backref='teacher',lazy='dynamic')
    #声明和特殊休息时间表的一对多关系
    special_rest = db.relationship('SpecialRest',backref='teacher',lazy='dynamic')
    #声明和补班时间表的一对多关系
    make_up_time = db.relationship('MakeUpTime',backref='teacher',lazy='dynamic')
    #逻辑删除
    is_delete = db.Column(db.Boolean,default=False)

    def __init__(self,**kwargs):
        '''这是初始化方法'''
        super(User,self).__init__(**kwargs)
        #新注册的用户默认角色都是visitor
        visitor = Role.query.filter_by(default=True).first()
        self.role = visitor

    
    @property
    def password(self):
        '''这个方法是get密码，但我们是不允许读取密码的，所以一旦调用直接抛出异常'''
        raise AttributeError('密码不可读')

    @password.setter
    def password(self,password):
        '''
        这个方法是设置密码
        
        :参数 password:这是用户注册时提供的密码，我们会把它转化为hash值并保存起来
        '''
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        '''
        这是验证密码是否正确的方法
        
        :参数 password:这是用户登录或者进行其他验证操作时提供的密码，
        该方法会验证这个密码是否正确,并根据实际情况返回True或者False
        '''
        return check_password_hash(self.password_hash,password)



    def can(self,permission):
        '''
        这是用户检查用户是否拥有某项权限的方法，返回布尔值

        :参数 permission:某项权限的值
        '''
        return self.role is not None and (self.role.permissions & permission)== permission
    
    def is_admin(self):
        '''这是自定义的判断是否是管理员的方法'''
        return self.can(Permission.ADMINISTRATOR)

    def generate_confirm_token(self,expiration=3600):
        '''这是生成用于确认账号的口令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        token=s.dumps({'confirm':self.id})
        return token
    
    @staticmethod
    def confirm(token):
        '''这是验证口令，确认账号的方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False,'wrong token'
        id=data.get('confirm')
        user=User.query.get(id)
        if user:
            user.confirmed=True
            db.session.add(user)
            return True,user.username
        else:
            return False,'nobody'
    
    def generate_reset_password_token(self,expiration=3600):
        '''这是生成用于重置密码的口令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        token=s.dumps({'reset':self.id})
        return token

    @staticmethod
    def reset_password(token,new_password):
        '''这是重置密码的静态方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        id=data.get('reset')
        user=User.query.get(id)
        if user:
            user.password=new_password
            db.session.add(user)
            return True
        else:
            return False

    def generate_reset_email_token(self,new_email,expiration=3600):
        '''这是生成修改邮箱口令的方法'''
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        token=s.dumps({'change_email':self.id,'new_email':new_email})
        return token

    def reset_email(self,token):
        '''这是修改邮箱的方法'''
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('change_email')!=self.id:
            return False
        new_email=data.get('new_email')
        if new_email is None:
            return False
        #可能学生提交新邮箱的时候那个邮箱还没有被用，但是确认修改邮箱的时候已经被占用了，
        # 所以还是要检查一下
        if User.query.filter_by(email=new_email).first():
            return False
        self.email=new_email
        db.session.add(self)
        return True

    @staticmethod
    def validate_image(filename):
        '''这是对头像的进一步验证，主要是保证文件名合法，并且唯一'''  
        ALLOWED_EXTENSIONS=['jpg','jpeg','png','gif']
        #文件是否是图片
        if '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS:
            #把文件名变成安全的格式，防止xss攻击
            filename=secure_filename(filename)
            #查看文件名是否跟数据库里已经存在的重复了
            if User.query.filter_by(image=filename).first():
                random.seed()
                random_source='QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890'
                random_prefix=''
                #生成一个长度为6的随机前缀
                for _ in range(6):
                    random_prefix+=random.choice(random_source)
                #把这个随机前缀加到已经是安全格式的文件名前面
                filename=random_prefix+filename
            return filename
        else:
            raise ValidationError('You can only upload jpg, jpeg, png and gif')
        
        

    def __repr__(self):
        '''返回字符串描述'''
        return '<User %s>'%self.username


class AnonymousUser(AnonymousUserMixin):
    '''这是自定义的匿名用户类，继承自flask-login提供的基类'''
    def can(self,permission):
        return False
    def is_admin(self):
        return False

#把我们自定义的匿名用户赋给login_manager里的匿名用户属性
login_manager.anonymous_user = AnonymousUser

#加载用户时的回调函数
@login_manager.user_loader
def load_user(user_id):
    '''这是自定义的回调函数，
    按照规定它必须接受用户id作为参数,
    并返回用户对象本身'''
    return User.query.get(int(user_id))

class WorkTime(db.Model):
    '''这是老师的以星期为单位的常规工作时间的模型类'''
    __tablename__ = 'worktime'
    id=db.Column(db.Integer,primary_key=True)
    teacher_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    work_time=db.Column(db.String(512))

    def __repr__(self):
        '''返回的字符串描述'''
        return '<WorkTime %s>'%(self.teacher.username)

class SpecialRest(db.Model):
    '''这是老师的特殊休息时间，以年月日小时为单位'''
    __tablename__ = 'specialrest'
    id = db.Column(db.Integer,primary_key = True)
    teacher_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    #这个字段保存具体的特殊休息时间，保存的是datetime对象
    rest_time = db.Column(db.DateTime)
    type = db.Column(db.String(8))
    #这个字段是是否过期，如果某次请假已经是过去的事情了，就不需要再查询这个数据
    expire = db.Column(db.Boolean,default=False)

    def __repr__(self):
        '''返回的字符串描述'''
        return "<SpecialRest %s>"%(self.teacher.username)

class MakeUpTime(db.Model):
    '''这是老师的补班时间，以年月日小时为单位'''
    __tablename__ = 'makeuptime'
    id = db.Column(db.Integer,primary_key=True)
    teacher_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    #这个字段保存具体的补班时间，保存的是datetime对象
    make_up_time = db.Column(db.DateTime)
    #这个字段是是否过期，如果某次补班已经是过去的事情了，就不需要再查询这个数据
    expire = db.Column(db.Boolean,default=False)

    def __repr__(self):
        '''返回的字符串描述'''
        return "<MakeUpTime %s>"%(slef.teacher.username)




