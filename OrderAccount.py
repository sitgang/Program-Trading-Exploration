# -*- coding: utf-8 -*-
import os
import pandas as pd
pd.options.display.max_rows=10
from tushare import get_hist_data
import tushare as ts
import numpy as np
from indicators import indicators_for_dirverse,indicators_for_crosses
from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross
from colle_tool import mailhelper,save_report,toround,draw_candlestick
from pandas import DatetimeIndex
from dateutil.parser import parse
from prettytable import PrettyTable
from matplotlib.pyplot import plot,savefig 
import matplotlib
import matplotlib.pyplot as plt
from data_fetcher import fetch_all,fetch_one,get_stock_codes,normalize
from datetime import date
import uuid
import talib
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

class Order(object):
    
    def __init__(self):
        self.quantity=0#买入数量
        self.code='000000'#股票代码
        self.in_price=0.0#买入价
        self.isnot_sold=True#没有卖出
        self.initial_amount=0#初始价值
        self.out_price=0#卖出价
        self.profit=0#赚取利润
        self.final_amount=0#卖出价值
        self.in_datetime=0#买入时间
        self.out_datetime=0#卖出时间
        self.loss_stop=0.1#止损位
        self.win_stop=1.0#止盈位
        
    def initialize(self,code,in_price,in_datetime,quantity,loss_stop=0.1,win_stop=1.0):
        self.code=str(code)#赋予股票代码
        self.in_price=in_price#赋予进入价格
        self.in_datetime=in_datetime#赋予进入时间
        self.quantity=quantity#赋予买入数量
        self.isnot_sold=True#没有卖出
        self.initial_amount=self.in_price*self.quantity#赋予初始价值
        self.loss_stop=loss_stop#赋予止损位
        self.win_stop=win_stop#赋予止盈位
        
    def liquidate(self,out_price,out_datetime):
        self.out_price=out_price#赋予出场价格
        self.out_datetime=out_datetime#赋予出场时间
        self.isnot_sold=False#已经卖出
        self.profit=(self.out_price-self.in_price)*self.quantity#赚取利润
        self.final_amount=self.out_price*self.quantity#卖出价值



class Account(object):

    
    def __init__(self,init_q=1000000.0,max_po=10.0,df=None):
        self.initial_amount=init_q #初始金额
        self.gross_amount=init_q#总金额
        self.cash_amount=init_q#现金金额
        self.stock_amount=0.0#股票价值
        self.codes=set()
        self.max_position=max_po#最大持仓
        self.left_position=max_po#剩余仓位
        self.occupied_position=0#已占仓位
        self.money4one=float(self.cash_amount)/float(self.left_position)#一只股票可以使用的资金
        self.dead_order=[]#已平仓订单
        self.active_order={}#未平仓订单
        self.action={}#日期和总金额
        self.cash_action={}#现金动态
        self.df=df#df
        self.is_full=False#是否满仓
    
    def order_in(self,order):
        if self.left_position<=0:
            self.is_full=True
           
        self.cash_amount-=order.initial_amount#现金价值转换为股票价值
        self.stock_amount+=order.initial_amount#股票价值增加
        self.left_position-=1#剩余仓位减一
        self.occupied_position+=1#占用仓位加一
        self.money4one=float(self.cash_amount)/float(self.left_position)#给一只股票准备的资金
        self.active_order[str(order.code)]=order#添加未平仓订单
        self.codes.add(order.code)

        return self
            
    def order_out(self,order):
        
        self.gross_amount+=order.profit #账户利润增加
        self.cash_amount+=order.final_amount#股票价值转为现金价值
        self.stock_amount-=order.final_amount#股票价值减少
        self.left_position+=1#剩余仓位加一
        self.occupied_position-=1#占用仓位减一
        
        self.money4one=float(self.cash_amount)/float(self.left_position)#给一只股票准备的资金
        self.dead_order.append(order)#扔进已平仓股票中
        self.codes.remove(order.code)
        
        
        del self.active_order[order.code]
        
        if self.left_position>0:
            self.is_full=False
            
        return self
    
    #
    #def get_newest_value(self):
    #    
    #    if not self.codes:return
    #    #仓内没有股票
    #    
    #    n=date.now().isoformat()
    #    for code in self.codes:
    #        df=get_hist_data(code,start=n,ktype='15')
    #        if df.count()[0]<1:continue
    #        stock_value=9
    #        pass
            
    
    
    
    def show_orders(self):   
        row=PrettyTable(['in_datetime','code','in_price','quantity','out_datetime','out_price','profit'])
        
        for o in self.dead_order:
            row.add_row([o.in_datetime,o.code,o.in_price,int(o.quantity),o.out_datetime,o.out_price,o.profit])
        print row 
    
    def show_order(self,code):   
        
        row=PrettyTable(['in_datetime','code','in_price','quantity','out_datetime','out_price','profit'])
        for o in self.dead_order:
            if o.code==code:
                row.add_row([o.in_datetime,o.code,o.in_price,int(o.quantity),o.out_datetime,o.out_price,o.profit])
        print row            

    def codes_best_fit(self,n2show=10,fit=0.5):
        '''
        show_k : frequency you want to resample with
        '''
            
        data=[]
        for o in self.dead_order:
            data.append([o.in_datetime,o.code,o.in_price,int(o.quantity),o.out_datetime,o.out_price,o.profit])
        cols=['in_datetime','code','in_price','quantity','out_datetime','out_price','profit']
        df=pd.DataFrame(data,columns=cols)
        grouped=df.groupby(df['code'])
        
        def wr(df):
            return df[df.profit>0].count()/df.count()
            
        wrc=grouped.apply(wr)
        sr=pd.Series(wrc.iloc[:,1],name='WinRate')#每只股的胜率
        def ss(sr):return '%.2f%%'%(sr*100)#百分化输出

        
        sr=sr.sort_values(ascending=False)
        #sr=sr.apply(ss)

        dfc=grouped.count()
        sr1=pd.Series(dfc.iloc[:,1],name='TradeCounts')#交易次数
        
        df_descr=pd.concat([sr,sr1],axis=1)
        df_descr=df_descr.sort_values('WinRate',ascending=False)
        df=df_descr
        #return df_descr
        
        
        
        if fit:
            df=df[df.WinRate>=fit]
            
        if n2show:
            if df_descr.count()[0]>n2show:
                df=df[:n2show]
            elif df_descr.count()[0]<=n2show:
                df=df
        
        print '\n\n\n',df,'\n\n\n'    
        return df.index
        

        
        





    def pry_one(self,code,show_k='W'):
        '''
        show_k : frequency you want to resample with
        '''
            
        data=[]
        for o in self.dead_order:
            data.append([o.in_datetime,o.code,o.in_price,int(o.quantity),o.out_datetime,o.out_price,o.profit])
        cols=['in_datetime','code','in_price','quantity','out_datetime','out_price','profit']
        df=pd.DataFrame(data,columns=cols)
        df=df[df['code']==code]
        if df.count()[0]==0:return "You didn't test this stock"
        plt.figure(figsize=(20,6))
        ax=plt.axes()
        ax.xaxis_date()
        plt.scatter(list(df.in_datetime),df.in_price,marker='^',c='r',s=60,label='Buying')
        plt.scatter(list(df.out_datetime),df.out_price,marker='v',c='g',s=60,label='Selling')
        if show_k:
            if show_k==True:
                show_k='B'
            frame=fetch_one(code)
            frame=normalize(frame,show_k)
            draw_candlestick(frame,ax)
        plt.legend(loc=0)
        plt.title(str(code)+'  Trade Action')
    
    
    def show_return(self):
        
        sr=prof_float_sr(self)
        sr.index=pd.DatetimeIndex(sr.index)
        sr=sr+self.initial_amount
        sr.plot(figsize=(20,6),grid=True,c='r',label='Prof Value')
        plt.ylabel('Return')
        sr.cummax().plot(grid=True,c='g',label='Cummax Prof Value')
        plt.legend(loc=2)
        plt.title('Profolio Value')
    
    
    def test_report(self):
        
        data=[]
        
        for o in self.dead_order:
            data.append([o.in_datetime,o.code,o.in_price,int(o.quantity),o.out_datetime,o.out_price,o.profit])
        cols=['in_datetime','code','in_price','quantity','out_datetime','out_price','profit']
        df=pd.DataFrame(data,columns=cols)   
        df=df.set_index('out_datetime')
        df=df.sort_index()
        
        #start analyzing......
        
        cash_sr=pd.Series(self.cash_action)
        cash_sr.index=pd.DatetimeIndex(cash_sr.index)
        #账户现金
        
        float_sr=pd.Series(self.action)
        float_sr.index=pd.DatetimeIndex(float_sr.index)
        #浮动账户价值

        
        
        wc=[]
        lc=[]
        win_counter=0
        lose_counter=0

        for i in list(df.profit):
            if i>=0:
                win_counter+=1
                lc.append(lose_counter)
                lose_counter=0
            elif i<0:
                lose_counter+=1
                wc.append(win_counter)
                win_counter=0
                
        max_continuous_winning=max(wc)
        #最大连赢次数
        max_continuous_losing=max(lc)
        #最大连亏次数
        max_individual_win=max(df.profit)
        #最大单次盈利
        max_individual_lose=min(df.profit)
        #最大单次亏损
        num_trade=df.count()[0]
        #总的交易次数
        num_win_trade=df[df.profit>0].count()[0]
        #盈利交易次数
        num_lose_trade=df[df.profit<0].count()[0]
        #亏损交易次数
        
        
        
        
        starting_point=min(df.in_datetime.apply(pd.to_datetime)).strftime('%Y-%m-%d')
        ending_point=max(DatetimeIndex(df.index)).strftime('%Y-%m-%d')
        #回测开始结束时间
        lasting_days=(max(df.index)-min(df.in_datetime)).days
        #持续时间(天数）
        lasting_years=lasting_days/365.0
        #持续时间（年数）
        average_position='%.2f%%'%((1-np.mean(cash_sr/float_sr))*100)
        #平均持仓量
        max_position='%.2f%%'%((1-np.min(cash_sr/float_sr))*100)
        #最大持仓量
        annual_num_trade=num_trade/lasting_years
        #年均交易次数
        
        win_ratio='%.2f%%'%((num_win_trade/float(num_trade))*100)
        #胜率
        ave_return=np.mean(df.profit)
        #平均利润
        annualized_return=np.power(float_sr[-1]/float_sr[0],lasting_years)-1
        #年化收益率
        aw_al=(np.mean(df[df.profit>0]['profit']))/(-np.mean(df[df.profit<0]['profit']))
        aw_al='%.2f%%'%(aw_al*100)
        #均盈利/均亏损
        
        max_dropdown=max(1-(float_sr/float_sr.cummax()))
        #最大回撤幅度
        se=1-(float_sr/float_sr.cummax())
        worst_dropdown_date1=se[se==se.max()].index.to_pydatetime()[0]
        worst_dropdown_date=worst_dropdown_date1.strftime('%Y-%m-%d')
        #最大回撤出现时点
        se=float_sr.cummax()[float_sr.cummax()==float_sr.cummax()[worst_dropdown_date]]
        worst_dropdown_forming_days=(worst_dropdown_date1-se.index[0]).days
        #最大回撤形成时间
        worst_dropdown_recover_days=(se.index[-1]-worst_dropdown_date1).days
        #最大回撤恢复时间
        
        
        pt=PrettyTable()
        c1=['最大连赢次数','最大连亏次数','最大单次盈利','最大单次亏损',
            '总的交易次数','盈利交易次数','亏损交易次数']
        c2=[max_continuous_winning,max_continuous_losing,max_individual_win,max_individual_lose,
            num_trade,num_win_trade,num_lose_trade]
        c3=['回测开始时间','回测结束时间','持续时间(天数）','持续时间（年数）',
            '平均持仓量','最大持仓量','年均交易次数']
        c4=[starting_point,ending_point,lasting_days,lasting_years,average_position,
            max_position,annual_num_trade]
        c5=['胜率','平均利润','年化收益率','均盈利/均亏损','最大回撤幅度','最大回撤出现时点',
            '最大回撤形成时间',',最大回撤恢复时间']
        c6=[win_ratio,ave_return,annualized_return,aw_al,
            max_dropdown,worst_dropdown_date,
            worst_dropdown_forming_days,worst_dropdown_recover_days]

        pt.add_column('回测指标',c1+c3+c5)
        pt.add_column('参考数值',map(toround,c2+c4+c6))
        
        save_report(str(pt))
        
        sr=prof_float_sr(self)
        sr.index=pd.DatetimeIndex(sr.index)
        sr=sr+self.initial_amount
        sr.plot(figsize=(20,6),grid=True,c='r')
        plt.ylabel('Return')
        sr.cummax().plot(grid=True,c='g')
        
        plt.legend(loc=2)
        plt.title('Profolio Value')
        
        pic_name=str(uuid.uuid1())
        pic_path='/Users/xuegeng/Desktop/zshingen_right/Reports/%s.jpg'%pic_name
        savefig(pic_path)
        
        sender=mailhelper()
        sender.send_mail(['621181828@qq.com'],'回测报告',content=str(pt),pic_path=pic_path)
  
    
def prof_float_sr(acc):
    
        src=[]
        for o in acc.dead_order:
            
            sr=acc.df[acc.df.code==o.code].close
            sr.index=pd.to_datetime(sr.index)
            sr=sr.sort_index()
            sr.index=pd.to_datetime(sr.index)
            s1=sr[o.in_datetime:o.out_datetime]
            s1.index=pd.to_datetime(s1.index)
            s1=s1.sort_index()
            s2=s1-s1[0]
            s3=pd.Series(index=pd.date_range('2010-01-01','2015-12-31'),data=[0])
            s4=(s2+s3).fillna(method='ffill').fillna(method='bfill')
    
            src.append(s4*o.quantity)
        
        s3=pd.Series(index=pd.date_range('2010-01-01','2015-12-31'),data=[0])
        for sr in src:
            s3=s3+sr
        
        return s3