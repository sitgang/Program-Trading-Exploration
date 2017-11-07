# -*- coding: utf-8 -*-
import os
import pandas as pd
pd.options.display.max_rows=10
import random
import tushare as ts
import numpy as np
#from OrderAccount import Account,Order
from indicators import indicators_for_dirverse,indicators_for_crosses
from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross
from pandas import DatetimeIndex
from dateutil.parser import parse
from prettytable import PrettyTable
import matplotlib
import matplotlib.pyplot as plt
import talib
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

names=['date','time','open','high','low','close','volume','amount']



def get_stock_codes(markets=['zz500s'],ipo_date=None):
    '''
    markets: list
    e.g.['sme','gem','st','hs300s','sz50s','zz500s','general'];
    ipo_date: str
    e.g.'2015-03-30'
    '''
    code_list=[]
    if 'sme' in markets:#中小板
        path='/Users/xuegeng/StockCodes/sme.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    if 'gem' in markets:#创业板
        path='/Users/xuegeng/StockCodes/gem.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    if 'st' in markets:#风险板
        path='/Users/xuegeng/StockCodes/st.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    if 'hs300s' in markets:#沪深300
        path='/Users/xuegeng/StockCodes/hs300s.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    if 'sz50s' in markets:#上证50
        path='/Users/xuegeng/StockCodes/sz50s.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    if 'zz500s' in markets:#中证500
        path='/Users/xuegeng/StockCodes/zz500s.csv'
        sr1=pd.read_csv(path,names=['n','code'])
        codes=list(sr1['code'])
        code_list.extend(codes)
    
    if ipo_date:
        new_stock_df=ts.new_stocks()
        new_stock_df=new_stock_df[new_stock_df['ipo_date']>ipo_date]
        new_stock_codes=list(new_stock_df.code)
    #得到输入时间之后发行的股票
    
        code_list=list(set(code_list))
        desired_codes=list(set(code_list)-set(new_stock_codes))
    #剔除新股
    
    desired_codes=list(set(code_list))
    
    return desired_codes

def fetch_one(code):
    try:
        df=pd.read_hdf('/Volumes/ETHANDISK/WholeData/%s.h5'%code)
        df['code']=code
        return df
    except:
        pass





#对df进行一些标准化处理
def normalize(df,freq='B'):
    '''freq:str  "B" for business day
                 "W" for week
                 "T for minite"
                 "H" for hour
    ==================================
    return : DataFrame normalized'''
    
    df=df.sort_index(ascending=False)
    ls=[df[['open']].resample(freq,how='first'),
    df[['high']].resample(freq,how='max'),
    df[['low']].resample(freq,how='min'),
    df[['close']].resample(freq,how='last')]
    
    mature_df=pd.concat(ls,axis=1)
    mature_df['code']=df.code[0]
    
    df=mature_df.dropna()
    return df
def fetch_all(codes,
                freq='B',
                indi=indicators_for_dirverse,
                refer1=diverse_strategy_buy,
                refer2=diverse_strategy_sell
                ):
    
    df_list=[]
    for code in codes:
        
        df=fetch_one(code) 
              
        df=normalize(df,freq=freq)
        df=df.dropna()
        df=indi(df)
        df=refer1(df)
        df=refer2(df)
            
        df_list.append(df)
    
    df_all=pd.concat(df_list)
    return df_all



def test_engine(df):
    
    account=Account()
    
    
    date_array=list(set(df.index))

    date_array.sort()
    for dateid in date_array:
        
        frame=df[df.index==dateid]  #该时间点所有股票的实时k线
        
        buy_frame=frame[frame['buy_signal']] #出现买入信号的股票的k线
        
        sell_frame=frame[frame['sell_signal']] #出现买入信号的股票的k线
        
        #先卖
        if sell_frame.count()[0]>0:
            codes=list(set(account.active_order.keys())&set(sell_frame.code))
            if len(codes)>0:    #仓中股票与可以卖的股票的交集
                for code in codes:
                    
                    order=account.active_order[str(code)] #从账户中取出交易单
                        
                    indate=order.in_datetime.date()
                    outdate=dateid.date()
                        
                    if indate==outdate:   #T+1 当天不能卖出
                        continue
                        
                    code_frame=frame[frame['code']==code]  
                        
                    out_price=code_frame.loc[dateid,'close']  #取出该股票的收盘价
                    order.liquidate(out_price,dateid)     #交易单平仓
                    account.order_out(order) 
                
                    account.is_full=False
                account.action[dateid]=account.gross_amount #gross 此时不会变
        
        #再买
        if buy_frame.count()[0]>0 and not account.is_full:
            for code in np.array(buy_frame.code):
                
                code_frame=frame[frame['code']==code]
                in_price=code_frame.loc[dateid,'close']
                money4one=account.money4one
                if np.isnan(money4one):print code
                shares=money4one/in_price
                if np.isnan(shares):
                    continue
                if np.isnan(shares):print code
                order=Order()
                
                order.initialize(code,in_price,dateid,shares)
                try:
                    account.order_in(order)
                except ZeroDivisionError:
                    continue
                
            account.action[dateid]=account.gross_amount
        
        
        random_frame=df[str(dateid)]
        codes=account.active_order.keys()
        if len(codes)>0:
            profit=0
            for code in codes:
                code_frame=random_frame[random_frame['code']==int(code)]
                order=account.active_order[code]
                in_price=order.in_price
                try:
                    now_price=code_frame.loc[str(dateid),'close']
                except KeyError:
                    #now_price=in_price
                    print account.active_order,codes
                    break
                profit+=order.quantity*(now_price-in_price)
                
            
            profit+=account.gross_amount
            account.action[dateid]=profit
    return account      

class Order(object):
    
    def __init__(self):
        self.quantity=0
        self.code='000000'
        self.in_price=0.0
        self.isnot_sold=True
        self.initial_amount=0
        self.out_price=0
        self.profit=0
        self.final_amount=0
        self.in_datetime=0
        self.out_datetime=0
        
    def initialize(self,code,in_price,in_datetime,quantity):
        self.code=str(code)
        self.in_price=in_price
        self.in_datetime=in_datetime
        self.quantity=quantity
        self.isnot_sold=True
        self.initial_amount=self.in_price*self.quantity
        
    def liquidate(self,out_price,out_datetime):
        self.out_price=out_price
        self.out_datetime=out_datetime
        self.isnot_sold=False
        self.profit=(self.out_price-self.in_price)*self.quantity
        self.final_amount=self.out_price*self.quantity



class Account(object):

    
    def __init__(self,init_q=1000000.0,max_po=10.0):
        self.initial_amount=init_q #初始金额
        self.gross_amount=init_q#总金额
        self.cash_amount=init_q#现金金额
        self.stock_amount=0.0#股票价值
        self.max_position=max_po#最大持仓
        self.left_position=max_po#剩余仓位
        self.occupied_position=0#已占仓位
        self.money4one=float(self.cash_amount)/float(self.left_position)#一只股票可以使用的资金
        self.codes=[]#仓内股票
        self.dead_order=[]#已平仓订单
        self.active_order={}#未平仓订单
        self.action={}#日期和总金额
        self.is_full=False#是否满仓
    
    def order_in(self,order):
        self.cash_amount-=order.initial_amount
        self.stock_amount+=order.initial_amount
        self.left_position-=1
        self.occupied_position+=1
        self.money4one=float(self.cash_amount)/float(self.left_position)
        self.codes.append(order.code)
        self.active_order[str(order.code)]=order
        #if not np.isnan(self.gross_amount):
        #    self.action[order.in_datetime]=self.gross_amount
        if self.left_position==0:
            self.is_full=True
            
    def order_out(self,order):
        self.gross_amount+=order.profit
        self.cash_amount+=order.final_amount
        self.stock_amount-=order.final_amount
        self.left_position+=1
        self.occupied_position-=1
        try:
            self.money4one=float(self.cash_amount)/float(self.left_position)
        except ZeroDivisionError:
            self.money4one=float(self.cash_amount)
            self.left_position=1
        self.codes.remove(order.code)
        self.dead_order+=[order]
        del self.active_order[order.code]
        #if not np.isnan(self.gross_amount):
        #    self.action[order.out_datetime]=self.gross_amount
        if self.left_position>0:
            self.is_full=False
    
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

    def pry_one(self,code,show_k=False):
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
        plt.scatter(list(df.in_datetime),df.in_price,marker='^',c='r',s=60)
        plt.scatter(list(df.out_datetime),df.out_price,marker='v',c='g',s=60)
        if show_k:
            if show_k==True:show_k='B'
            frame=fetch_one(code)
            frame=normalize(frame,show_k)
            draw_candlestick(frame,ax)
            
    
        
def draw_candlestick(df,ax):#df已被规范化，时间序列的ohlcva

    '''
    用于画出蜡烛图，但过长的蜡烛图容易变慢
    注意：当你传入的是groupby对象时，要用reset_index转化为dateframe
    '''
    df['date_time']=df.index
    
    quotes=df[['date_time','open','high','low','close']].values
    
    tuples = [tuple(x) for x in quotes]
    
    qw=[]
    
    for things in tuples:
        date=matplotlib.dates.date2num(things[0])
        tuple1=(date,things[1],things[2],things[3],things[4])
        qw.append(tuple1)
    
    #fig, ax = plt.subplots()
    
    ax.xaxis_date()
    ax.grid(linestyle='-', linewidth=0.2)
    matplotlib.finance.candlestick_ohlc(ax, qw, width=.5, colorup='r',colordown='g', alpha =.4)            
                
                        
#codes=get_stock_codes('sz50s')
#all_df=fetch_all(codes_list,indi=indicators_for_crosses,refer1=golden_cross,refer2=dead_cross)
#acc=test_engine(all_df)


#sr=pd.Series(acc.action)
#sr.index=pd.DatetimeIndex(sr.index)
#sr.plot(figsize=(20,6),grid=True,c='r')
#plt.ylabel('Return')
#sr.cummax().plot(grid=True,c='g')


    
    
    

    
def win_count(acc):
    win=0
    lose=0
    for order in acc.dead_order:
        if order.profit>0:
            win+=1
        else:
            lose+=1
    return float(win)/(win+lose)


def show_acc(acc):   
    row=PrettyTable(['in','code','inp','v','ou','onp'])
        
    for o in acc.dead_order:
        row.add_row([o.in_datetime,o.code,o.in_price,o.quantity,o.out_datetime,o.out_price])
    print row
    