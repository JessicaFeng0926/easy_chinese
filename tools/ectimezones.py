import pytz,json,os

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


      
       