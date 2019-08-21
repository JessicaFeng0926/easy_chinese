import os


class Config():
    '''基本配置'''
    #这是设置的一个密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a very hard to guess string'
    #确保提交到数据库会话里的数据最后都会自动提交到数据库
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    #邮件主题前缀配置
    EC_MAIL_SUBJECT_PREFIX = '[Easy Chinese]'
    #本站邮件发送者
    EC_MAIL_SENDER = os.environ.get('MAIL_USERNAME')
    #本站管理员
    EC_ADMIN = os.environ.get('EC_ADMIN')

    @staticmethod
    def init_app(app):
        '''这是初始化app的静态方法'''
        pass

class DevelopmentConfig(Config):
    '''这是开发环境的配置，继承自基本配置'''
    #开启调试模式
    DEBUG = True
    #配置邮箱的服务器和端口
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    #开启邮箱的SSL加密
    MAIL_USE_SSL = True
    #获取本站邮箱的用户名和密码
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    #配置用于开发环境的数据库的路径
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:19690607@localhost/ecdev'

class TestingConfig(Config):
    '''这是测试环境的配置，继承自基本配置'''
    #声明是测试环境
    TESTING = True
    #关闭csrf验证，避免繁琐的操作
    WTF_CSRF_ENABLED = False
    #配置用于测试环境的数据库的路径
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:19690607@localhost/ectest'

class ProductionConfig(Config):
    '''这是生产环境的配置，继承自基本配置'''
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:19690697@localhost/ecpro'

#这个字典是为了导入类方便
config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopmentConfig,
}



