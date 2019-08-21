from flask import Blueprint
from ..models import Permission

#实例化蓝本，命名为'main',第二个参数告知蓝本所在的模块
main=Blueprint('main',__name__)

#导入视图和错误处理函数
from . import views,errors

#用上下文处理器使得在所有模板中都可以用Permission类来检验权限
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)