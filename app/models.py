from . import db,login_manager
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from datetime import datetime

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

