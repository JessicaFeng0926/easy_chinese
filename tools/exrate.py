import requests
from bs4 import BeautifulSoup
import math
import decimal

#从国家外汇管理局网站把美元的汇率爬下来
res = requests.get('http://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do')
soup = BeautifulSoup(res.text,'html.parser')
tds = soup.select('#InfoTable td')
#表格里的第一个td单元格里存放的就是美元的汇率，是100美元能兑换多少人民币
rate = decimal.Decimal(tds[1].text.strip())/decimal.Decimal(100)


def dollar_2_rmb(dollar):
    '''这是把美元根据当前汇率转化为人民币的函数'''
    return round(float(decimal.Decimal(dollar)*rate),2)
    