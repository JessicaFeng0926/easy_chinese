from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from config import config
from flask import Flask

#实例化我们需要用到的类
bootstrap=Bootstrap()
mail=Mail()
moment = Moment()
db=SQLAlchemy()
login_manager=LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    '''
    这是创建app的函数

    :参数 config_name:配置的名字，就是config字典里的键
    '''
    #创建app,给它一个特定的配置，并且初始化这个app（在我们的程序里，初始化其实什么也没做）
    app=Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    #初始化上面创建的那些扩展类的实例
    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)

    #注册蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')

    from .visitor import visitor as visitor_blueprint
    app.register_blueprint(visitor_blueprint,url_prefix='/visitor')

    from .student import student as student_blueprint
    app.register_blueprint(student_blueprint,url_prefix='/student')
    
    from .teacher import teacher as teacher_blueprint
    app.register_blueprint(teacher_blueprint,url_prefix='/teacher')
    
    return app



