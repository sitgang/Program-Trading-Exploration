# -*- coding: utf-8 -*-
import os
import pandas as pd
pd.options.display.max_rows=10
import tushare as ts
import numpy as np
from OrderAccount import Account,Order
from indicators import indicators_for_dirverse,indicators_for_crosses
from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross,dead_cross
import colle_tool
from dateutil.parser import parse
from colle_tool import mailhelper,save_report,toround,draw_candlestick
from pandas import DatetimeIndex
from dateutil.parser import parse
from prettytable import PrettyTable
from matplotlib.pyplot import plot,savefig 
import matplotlib
import matplotlib.pyplot as plt
from data_fetcher import fetch_all,fetch_one,get_stock_codes,normalize
import uuid
import talib
import sys
from datetime import datetime
reload(sys)
sys.setdefaultencoding('utf-8')

def test_engine(df,
                initial_money=100000,
                max_position=10,
                cross_confirm=False,
                df2=None,
                loss_stop=0.1,
                win_stop=1.0):
    
    '''
    cross_confirm in [Min','H','D','M']
    DF2 是你希望确认的时间框架的数据
    
    '''
    cross_format={'Min':'%Y-%m-%d %H:%M',
                  'H':'%Y-%m-%d %H',
                  'D':'%Y-%m-%d',
                  'M':'%Y-%m'}
    
    
    
    df=df[['close','code','buy_signal','sell_signal']]
    
    
    account=Account(initial_money,max_position,df=df)
    
    date_array=list(set(df.index))
    date_array.sort()
    
    
    
    
    for dateid in date_array:
        
        dateid=dateid.to_datetime()

        
        frame=df[dateid.isoformat()]  #该时间点所有股票的实时k线
        buy_frame=frame[frame['buy_signal']] #出现买入信号的股票的k线
        sell_frame=frame[frame['sell_signal']] #出现买入信号的股票的k线
        
        #先卖
        if sell_frame.count()[0]>0:
            if len(account.active_order.keys())>0 and len(sell_frame.code)>0:
                sell_codes=list(set(map(str,account.active_order.keys())).intersection(set(map(str,sell_frame.code))))
            else:sell_codes=[]
            if len(sell_codes)>0:    #仓中股票与可以卖的股票的交集
                for sell_code in sell_codes:
                    order=account.active_order[str(sell_code)] #从账户中取出交易单
                        
                    indate=order.in_datetime.date()
                    outdate=dateid.date()
                        
                    if indate==outdate:   #T+1 当天不能卖出
                        continue
                        
                    code_frame=frame[frame.code==sell_code]
                    if len(code_frame)<1:print sell_code  
                    try:    
                        out_price=code_frame['close'][0]#取出该股票的收盘价
                    except IndexError:
                        
                        print "NOT SOLD"
                        continue
                    order.liquidate(out_price,dateid)#.isoformat())     #交易单平仓
                    
                    account=account.order_out(order) 
                    account.is_full=False
                account.action[dateid.isoformat()]=account.gross_amount
                
        #再买
        if buy_frame.count()[0]>0 and not account.is_full:
            for buy_code in list(set(buy_frame.code)):
                if str(buy_code) in account.active_order.keys():
                    continue
                if len(account.active_order.keys())>=10:
                    break
                if account.gross_amount<=0 and account.cash_amount<=0:
                    break
                
                code_frame=frame[frame.code==buy_code]
                
                try:
                    in_price=code_frame['close'][0]
                except IndexError:
                    print "NOT BROUGHT"
                    continue
                money4one=account.money4one
                if np.isnan(money4one):
                    print buy_code
                shares=money4one/in_price
                if np.isnan(shares):
                    print buy_code
                order=Order()
                
                order.initialize(str(buy_code),in_price,dateid,shares,loss_stop=loss_stop,win_stop=win_stop)
                
                if cross_confirm:#跨时间框架确认
                    s=df2[dateid.strftime(cross_format[cross_confirm])]
                    cross_true=s[(s.code==600000)&(s['buy_signal'])]
                    cross_true=cross_true.dropna()
                    cross_true=cross_true.count()[0]
                else:cross_true=True
                if account.left_position>1 and cross_true:
                    account=account.order_in(order)
            #account.action[dateid]=account.gross_amount
        
        retri_codes=account.active_order.keys()
        if len(retri_codes)>0:
            profit=0
            for retri_code in account.active_order.keys():
                try:
                    order1=account.active_order[str(retri_code)]
                except KeyError:
                    print retri_code,dateid.isoformat(),'   DAILY RETRIVE ERROR'#,account.active_order.keys()
                    continue
                in_price=order1.in_price
                try:
                    df2=frame[frame.code==retri_code]
                    now_price=df2['close'][0]
                except IndexError:
                    print 'NOT RECORDED'
                    now_price=in_price
                
                decisive_ratio=((order1.quantity*(now_price))/float(order1.initial_amount))
                if decisive_ratio<(1-order1.loss_stop):
                
                    order1.liquidate(now_price,dateid)#.isoformat())     #交易单平仓
                    try:
                        account=account.order_out(order1) 
                        
                    except KeyError:
                        print retri_code,dateid.isoformat(),'    LOSS STOP ERROR',account.active_order.keys()
                     
                if decisive_ratio>(1+order1.win_stop):
                
                    order1.liquidate(now_price,dateid)#.isoformat())     #交易单平仓
                    account=account.order_out(order1) 
                    account.is_full=False  
                
                            
                
                profit+=order1.quantity*(now_price-in_price)
                
            
            profit+=account.gross_amount
            account.action[dateid.isoformat()]=profit
            account.cash_action[dateid.isoformat()]=account.cash_amount
            #if len(account.active_order.keys())>10:print account.active_order.keys()
            #else:print 'GOOD'
            #20160707 买入股票数量在限制范围内,少数股天无法取得价格
    return account      

                 
#codes=get_stock_codes('sz50s')
#all_df=fetch_all(codes_list,indi=indicators_for_crosses,refer1=golden_cross,refer2=dead_cross)
#acc=test_engine(all_df)
