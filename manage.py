from app import create_app,db
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand
import os
from app.models import Role,User,WorkTime,SpecialRest,MakeUpTime,Lesson,StudentProfile


#创建app
app = create_app(os.environ.get('EC_CONFIG') or 'default')

#初始化命令行和迁移
manager=Manager(app)
migrate=Migrate(app,db)

def make_shell_context():
    return dict(app=app,db=db,Role=Role,User=User,WorkTime=WorkTime,SpecialRest=SpecialRest,MakeUpTime=MakeUpTime,Lesson=Lesson,StudentProfile=StudentProfile)

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




