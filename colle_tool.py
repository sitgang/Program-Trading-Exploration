
# -*- coding: utf-8 -*-
import smtplib  
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText  
from email.mime.application import MIMEApplication  
import datetime 
import matplotlib
import matplotlib.pyplot as plt
import threading
from threading import Thread  
from datetime import datetime
import tushare as ts
class mailhelper(object):
    '''
    这个类实现发送邮件的功能
    '''
    def __init__(self):

        self.mail_host="mail.bit.edu.cn"  #设置服务器
        self.mail_user="1120142875"    #用户名
        self.mail_pass="francium0426"   #密码
        self.mail_postfix="bit.edu.cn"  #发件箱的后缀

    def send_mail(self,to_list,sub,content='!',pic_path=None):
        me=u"Shingen Quant System"+"<"+self.mail_user+"@"+self.mail_postfix+">"
        
        msg = MIMEMultipart(_subtype='plain',_charset='utf-8')
        
        part = MIMEText(content)  
        msg.attach(part) 
        
        if pic_path:
            
            part = MIMEApplication(open(pic_path,'rb').read())  
            part.add_header('Content-Disposition', 'attachment', filename="FloatValue.jpg")  
            msg.attach(part)
        
        #msg = MIMEText(content,_subtype='plain',_charset='utf-8')
        msg['Subject'] = sub
        msg['From'] = me
        msg['To'] = ";".join(to_list)
        
         
        try:
            server = smtplib.SMTP()
            server.connect(self.mail_host)
            server.login(self.mail_user,self.mail_pass)
            server.sendmail(me, to_list, msg.as_string())
            server.close()
            return True
        except Exception, e:
            print str(e)
            return False

def save_report(content):
    n=datetime.datetime.now()
    path='/Users/xuegeng/Desktop/zshingen_right/Reports/r'+n.strftime('%Y%m%d%H%M%S')+'.txt'
    f=open(path,'w')
    f.write(content)
    f.close()

def toround(x):
    '''将浮点数取两位小数'''
    if isinstance(x,float):
        return round(x,2)
    else:return x

    
def draw_candlestick(df,freq = 'D'):#df已被规范化，时间序列的ohlcva

    '''
    if FREQ == 1min ,width ==0.0005,if D width == 0.5
    用于画出蜡烛图，但过长的蜡烛图容易变慢
    注意：当你传入的是groupby对象时，要用reset_index转化为dateframe
    '''
    df['date_time']=df.index
    
    quotes=df[['date_time','open','high','low','close']].values
    
    tuples = [tuple(x) for x in quotes]
    
    qw=[]
    
    freq_width_dict = {'D':0.5,'d':0.5,'1min':0.0005,'1Min':0.0005}
    
    for things in tuples:
        date=matplotlib.dates.date2num(things[0])
        tuple1=(date,things[1],things[2],things[3],things[4])
        qw.append(tuple1)
    
    fig, ax = plt.subplots()
    
    ax.xaxis_date()
    ax.grid(linestyle='-', linewidth=0.1)
    matplotlib.finance.candlestick_ohlc(ax, qw, colorup='r',colordown='g', alpha =.4, width=freq_width_dict[freq])
    

import shelve
class TimeoutException(Exception):
  pass
ThreadStop = Thread._Thread__stop#获取私有函数
def timelimited(timeout):
  def decorator(function):
    def decorator2(*args,**kwargs):
      class TimeLimited(Thread):
        def __init__(self,_error= None,):
          Thread.__init__(self)
          self._error = _error
        def run(self):
          try:
            self.result = function(*args,**kwargs)
          except Exception,e:
            self._error =e
        def _stop(self):
          if self.isAlive():
            ThreadStop(self)
      t = TimeLimited()
      t.start()
      t.join(timeout)
      if isinstance(t._error,TimeoutException):
        t._stop()
        raise TimeoutException('timeout for %s' % (repr(function)))
      if t.isAlive():
        t._stop()
        raise TimeoutException('timeout for %s' % (repr(function)))
      if t._error is None:
        return t.result
    return decorator2
  return decorator



def div_list(ls,n): 
    '''均分列表''' 
    if not isinstance(ls,list) or not isinstance(n,int):  
        return []  
    ls_len = len(ls)  
    if n<=0 or 0==ls_len:  
        return []  
    if n > ls_len:  
        return []  
    elif n == ls_len:  
        return [[i] for i in ls]  
    else:  
        j = ls_len/n  
        k = ls_len%n  
        ### j,j,j,...(前面有n-1个j),j+k  
        #步长j,次数n-1  
        ls_return = []  
        for i in xrange(0,(n-1)*j,j):  
            ls_return.append(ls[i:i+j])  
        #算上末尾的j+k  
        ls_return.append(ls[(n-1)*j:])  
        return ls_return   

#codes=get_codes()
#dcodes=div_list(codes,53)
#for code in dcodes:test(code)
    