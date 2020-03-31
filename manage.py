from app import create_app,db
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand
import os
from app.models import Role,User,WorkTime,SpecialRest,MakeUpTime,Lesson,StudentProfile,LessonRecord,Order
from flask_wtf.csrf import CSRFProtect

#创建app
app = create_app(os.environ.get('EC_CONFIG') or 'default')

# 保护app免受CSRF攻击，这主要是为Ajax请求提供便利的，form表单没有它也不会受到攻击
CSRFProtect(app)

#初始化命令行和迁移
manager=Manager(app)
migrate=Migrate(app,db)

def make_shell_context():
    return dict(
        app=app,
        db=db,
        Role=Role,
        User=User,
        WorkTime=WorkTime,
        SpecialRest=SpecialRest,
        MakeUpTime=MakeUpTime,
        Lesson=Lesson,
        StudentProfile=StudentProfile,
        LessonRecord=LessonRecord,
        Order = Order,
        )

#以后就不需要往shell里导入db了
manager.add_command('shell',Shell(make_context=make_shell_context))
#以后用db就可以代替迁移的命令了
manager.add_command('db',MigrateCommand)

@manager.command
def test():
    '''这是启动测试的函数'''
    import unittest
    #寻找所有tests文件夹里的脚本，逐个运行测试
    tests=unittest.TestLoader().discover('tests')
    unittest.TextTestRunner().run(tests)

if __name__ == '__main__':
    manager.run()




