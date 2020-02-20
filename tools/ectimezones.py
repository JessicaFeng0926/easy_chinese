import pytz,json,os
from datetime import datetime

""" ectimezone_list=[]

for country_name,timezone_list in pytz.country_timezones.items():
    if len(timezone_list)>1:
        num=0
        for timezone in timezone_list:
            ectimezone_list.append((country_name+'_'+str(num),timezone))
            num+=1        
    else:
        ectimezone_list.append((country_name,timezone_list[0])) """
#从JSON中读取我保存的时区信息
with open(r'D:\Python学习\flask_project\easy_chinese\app\static\json\ectimezones.json','r') as f:
    ectimezone_list=json.load(f)

#按照时区字母顺序排序，因为时区才是展示给用户的信息，需要好找一些
ectimezone_list=sorted(ectimezone_list,key=lambda x:x[1])


# 把数据库里存储的标准时间转化为用户的当地时间
def get_localtime(database_time,user):
    '''这是把数据库里存放的时间转化为用户当地时间的函数'''
    utc = pytz.timezone('UTC')
    tz = user.timezone
    if len(tz) ==2:
        tz = pytz.country_timezones[tz][0]
    else:
        tz = pytz.country_timezones[tz[:2]][int(tz[3:])]
    tz = pytz.timezone(tz)
    utctime = datetime(database_time.year,database_time.month,database_time.day,database_time.hour,tzinfo=utc)
    localtime = utctime.astimezone(tz)
    return localtime

# 把用户提交的自己视角的naive time转化为可以存储至数据库的UTC视角的naive time
def get_utctime(naive_localtime,user):
    '''从用户视角转化为UTC视角
    : 参数 naive_localtime:datetime对象，没有时区信息，但是以用户所在时区为标准
    : 参数 user:用户
    '''
    utc = pytz.timezone('UTC')
    tz = user.timezone
    if len(tz) ==2:
        tz = pytz.country_timezones[tz][0]
    else:
        tz = pytz.country_timezones[tz[:2]][int(tz[3:])]
    tz = pytz.timezone(tz)
    localtime = naive_localtime.astimezone(tz)
    utctime = localtime.astimezone(utc)
    utctime = datetime(utctime.year,utctime.month,utctime.day,utctime.hour)
    return utctime
    


       