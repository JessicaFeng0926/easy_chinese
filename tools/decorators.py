from functools import wraps
from flask_login import current_user
from app.models import Permission
from flask import abort

def permission_required(permission):
    '''这是权限装饰器'''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    '''必须是管理员'''
    return permission_required(Permission.ADMINISTRATOR)(f)