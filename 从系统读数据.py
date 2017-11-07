# -*- coding: utf-8 -*-
import os
import pandas as pd
import random
import tushare as ts
import numpy as np
from OrderAccount import Account,Order
from indicators import indicators_for_dirverse,indicators_for_crosses
from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross,dead_cross
from pandas import DatetimeIndex
from prettytable import PrettyTable
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
        df=ts.get_sme_classified()
        codes=list(df.code)
        code_list.extend(codes)
    if 'gem' in markets:#创业板
        df=ts.get_gem_classified()
        codes=list(df.code)
        code_list.extend(codes)
    if 'st' in markets:#风险板
        df=ts.get_st_classified()
        codes=list(df.code)
        code_list.extend(codes)
    if 'hs300s' in markets:#沪深300
        df=ts.get_hs300s()
        codes=list(df.code)
        code_list.extend(codes)
    if 'sz50s' in markets:#上证50
        df=ts.get_sz50s()
        codes=list(df.code)
        code_list.extend(codes)
    if 'zz500s' in markets:#中证500
        df=ts.get_zz500s()
        codes=list(df.code)
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


#检查是股票还是指数
def is_stock(df):
    if df['close'].mean()>1000:
        return False
    elif df['close'].mean()<500:
        return True
        
def is_index(df):
    if df['close'].mean()<1000:
        return False
    elif df['close'].mean()>1000:
        return True        

#取得单只股票的df
#def fetch_one(code):
#    
#    names=['date','time','open','high','low','close','volume','amount']
#    years=['2010','2011','2012','2013','2014','2015']
#    path_name='/Users/xuegeng/StockData/%s股票五分钟'
#    
#    df2concat=[]
#    
#    for year in years:
#        for root, dirs, files in os.walk(path_name%year):
#            for filename in files:
#                if code in filename:
#                    path=(path_name%year)+'/'+filename
#                    df=pd.read_csv(path,names=names,parse_dates=[[0,1]],infer_datetime_format=True,dtype=np.float64)
#                    if is_stock(df):
#                        df2concat.append(df)
#    try:
#        df_total=pd.concat(df2concat)
#        df_total['code']=code
#    except ValueError:return None
#    
#    return df_total


def fetch_one(code):
    try:
        df=pd.read_hdf('/Users/xuegeng/WholeData/%s.h5'%code)
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
    ls=[df[['open']].resample(freq).first(),
    df[['high']].resample(freq).max(),
    df[['low']].resample(freq).min(),
    df[['close']].resample(freq).last()]
    
    mature_df=pd.concat(ls,axis=1)
    
    #df=mature_df.resample(freq).first()
    df=mature_df.dropna()
    return df
def fetch_all(codes,freq='B',indi=indicators_for_dirverse,refer1=diverse_strategy_buy,refer2=diverse_strategy_sell):
    
    df_list=[]
    for code in codes:
        df=fetch_one(code) 
        try:      
            df=normalize(df,freq=freq)
            df=df.dropna()
            df=indi(df)
            df=refer1(df)
            df=refer2(df)
            
            df_list.append(df)
        except:pass
    if len(df_list)>1:
        return pd.concat(df_list)
    elif len(df_list)==1:
        return df_list[0]
    
#插入指标、策略类的参考
def insert_reference(frame,reference):
    """
    frame:DataFrame
    reference: insert method
    """
    frame=reference(frame)#插入参考
    frame=frame.dropna()
    return frame


def gene_pn(codes_list,freq='H',rand_num=0):
    '''
    codes_list:list of codes
    rand_num:number of codes you want to operate on
    '''
    codes_dict={}
    random.shuffle(codes_list)
    if rand_num>0:
        rand_codes=codes_list[:rand_num]
    else:
        rand_codes=codes_list
    #将list洗乱
    
    for code in rand_codes:
        df=fetch_one(code)       
        df=normalize(df,freq=freq)
        
        codes_dict[code]=df
    day_pn=pd.Panel(codes_dict)
    pn=day_pn.fillna(method='ffill')
    #日线数据
    return pn

#def get_stock_codes(markets, ipo_date=None):
#	'''
#    markets: list
#    e.g.['sme','gem','st','hs300s','sz50s','zz500s','general'];
#    ipo_date: str
#    e.g.'2015-03-30'
#    '''
#	code_list = []
#	if 'sme' in markets:  # 中小板
#		df = ts.get_sme_classified()
#		codes = list(df.code)
#		code_list.extend(codes)
#	if 'gem' in markets:  # 创业板
#		df = ts.get_gem_classified()
#		codes = list(df.code)
#		code_list.extend(codes)
#	if 'st' in markets:  # 风险板
#		df = ts.get_st_classified()
#		codes = list(df.code)
#		code_list.extend(codes)
#	if 'hs300s' in markets:  # 沪深300
#		df = ts.get_hs300s()
#		codes = list(df.code)
#		code_list.extend(codes)
#	if 'sz50s' in markets:  # 上证50
#		df = ts.get_sz50s()
#		codes = list(df.code)
#		code_list.extend(codes)
#	if 'zz500s' in markets:  # 中证500
#		df = ts.get_zz500s()
#		codes = list(df.code)
#		code_list.extend(codes)
#
#	if ipo_date:
#		new_stock_df = ts.new_stocks()
#		new_stock_df = new_stock_df[new_stock_df['ipo_date'] > ipo_date]
#		new_stock_codes = list(new_stock_df.code)
#		# 得到输入时间之后发行的股票
#
#		code_list = list(set(code_list))
#		desired_codes = list(set(code_list) - set(new_stock_codes))
#	# 剔除新股
#
#	desired_codes = list(set(code_list))
#
#	return desired_codes
def stra(df):
    df['buy_signal']=df['close']>1.03*df['low']
    df['sell_signal']=df['close']<0.95*df['high']
    return df


    
    
        

    
def insert_strategy(pn,strategy_indicators=indicators_for_dirverse,buy_strategy=diverse_strategy_buy,sell_strategy=diverse_strategy_sell):
    #用于插入策略
    
    dic={}
    #pn.major_axis=pd.DatetimeIndex(pn.major_axis)
    for code in pn.items:
        frame=pn[code]
        frame.index=DatetimeIndex(frame.index)
        
        if strategy_indicators:
        
            frame=strategy_indicators(frame)#插入指标
        frame=buy_strategy(frame)#插入买入策略
        frame=sell_strategy(frame)#插入卖出策略
        #frame.index=DatetimeIndex(frame.index)#
        frame=frame.dropna()
            
        dic[code]=frame
        
    pn=pd.Panel(dic)
    #pn.major_axis=pd.DatetimeIndex(pn.major_axis)
    pn=pn.fillna(method='ffill')
    return pn

def test_engine(df):
    
    account=Account()
    
    random_date=np.random.choice(list(df.index),400)
    
    df2=df[df['buy_signal']|df['sell_signal']]
    date_array=np.unique(list(df2.index))
    date_array=list(date_array)
    date_array.extend(list(random_date))
    date_array.sort()
    for dateid in date_array:
        dateid=str(dateid)
        frame=df2[dateid]
        buy_frame=frame[frame['buy_signal']]
        sell_frame=frame[frame['sell_signal']]
        #先卖
        codes=np.intersect1d(account.codes,np.array(sell_frame.code),assume_unique=True)
        if len(codes)>0:
            for code in codes:
                try:
                    order=account.active_order[code]
                    code_frame=frame[frame['code']==code]
                
                    out_price=code_frame.iloc[0,3]
                    order.liquidate(out_price,dateid)
                    account.order_out(order)
                    account.is_full=False
                except:pass
                account.action[dateid]=account.gross_amount
      
        
        #再买
        elif len(np.array(buy_frame.code))>0:
            for code in np.array(buy_frame.code):
                if account.is_full:
                    break
                code_frame=frame[frame['code']==code]
                in_price=code_frame.iloc[0,3]
                money4one=account.money4one
                shares=money4one/in_price
                order=Order()
                order.initialize(code,in_price,dateid,shares)
                account.order_in(order)
                account.action[dateid]=account.gross_amount
        
        
        else:
            random_frame=df[dateid]
            codes=account.codes
            if len(codes)>0:
                profit=0
                for code in codes:
                    try:
                        code_frame=random_frame[random_frame['code']==code]
                        order=account.active_order[code]
                        in_price=order.in_price
                        now_price=code_frame.iloc[0,3]
                        profit+=order.quantity*(now_price-in_price)
                    
                    except:pass
                profit+=account.gross_amount
                account.action[dateid]=profit
        account.action[dateid]=account.gross_amount
    return account      



#def run(pn,max_position=10):
#    '''
#    strategy runner
#    '''
#    global dy_amount
#    
#    buy_action={}
#    sell_action={}
#    dy_shares_buffer={}
#    dy_amount_action={}
#    dy_amount=10000000.0
#    idle_money=10000000.0
#    
#    #code_list=list(pn.items)
#    #random.shuffle(code_list)
#    
#    for timestamp in DatetimeIndex(pn.major_axis):
#        index_date=timestamp.to_datetime().strftime('%Y%m%d')
#        #先卖后买
#        
#        for code in dy_shares_buffer.keys():
#            frame = pn[code].loc[index_date:index_date]
#            sell_signal = frame['sell_signal'][0]
#            if sell_signal:
#                try:
#                    out_price = frame['close'][0]
#                    position = dy_shares_buffer[code]
#                    idle_money=idle_money+out_price*position
#                    
#                    sell_action[index_date] = (code,out_price,position)
#                    del dy_shares_buffer[code]
#                except : pass
#        
#        for code in list(set(pn.items)-set(dy_shares_buffer.keys())):
#            frame=pn[code].loc[index_date:index_date]         #某天的价格信息
#            buy_signal=frame['buy_signal'][0]
#            if buy_signal and len(dy_shares_buffer)<max_position:  #如果出现买入信号，且持仓小于最大持仓,执行买入
#                try :
#                    in_price=frame['close'][0]
#                    position = int(1/(10.0-len(dy_shares_buffer))*idle_money/in_price)  #买入的股数
#                    idle_money = idle_money-in_price*position                   #闲散资金
#                    
#                    buy_action[index_date] = (code,in_price,position)
#                    dy_shares_buffer[code]=position
#                except :pass
#        
#        position_value=0.0
#        for code in dy_shares_buffer.keys():
#            frame=pn[code].loc[index_date:index_date]
#            close_price=frame['close'][0]
#            position_value+=(close_price*dy_shares_buffer[code])
#        dy_amount=position_value+idle_money      #当日结束后股票与现金的总价值
#        
#        dy_amount_action[index_date]=dy_amount
#        
#    dy_amount_action_sr=pd.Series(dy_amount_action,name='dy_amount')#返回浮动盈利的时间序列
#    dy_amount_action_sr.index=DatetimeIndex(dy_amount_action_sr.index)
#    
#    buy_action_sr=pd.Series(buy_action,name='buy_action')#返回买入动作的时间序列
#    buy_action_sr.index=DatetimeIndex(buy_action_sr.index)
#    
#    sell_action_sr=pd.Series(sell_action,name='sell_action')#返回卖出动作的时间序列
#    sell_action_sr.index=DatetimeIndex(sell_action_sr.index) 
#      
#    return dy_amount_action_sr,buy_action_sr,sell_action_sr
#        
#                    
#def generate_win_counts(buy_action_sr,sell_action_sr):
#    #根据run()的输出生成获胜次数
#    
#    winning_counts=0
#    for timestp in buy_action_sr.index:
#        idx=timestp.strftime('%Y-%m-%d')
#        code=buy_action_sr[idx][0]
#        in_price=buy_action_sr[idx][1]
#        position=buy_action_sr[idx][2]
#        
#        for timestp2 in sell_action_sr.index:
#            idx2=timestp2.strftime('%Y-%m-%d')
#            code2=sell_action_sr[idx2][0]
#            out_price=sell_action_sr[idx2][1]
#            position2=sell_action_sr[idx2][2]
#            if code==code2 and in_price<out_price and position==position2:
#                winning_counts+=1
#                break
#    return winning_counts




#def generate_report(dy_amount_sr,buy_action_sr,sell_action_sr):
#    #根据run()的输出生成报告
#    
#    dy_amount_sr=dy_amount_sr.sort_index(ascending=True)
#    buy_action_sr=buy_action_sr.sort_index(ascending=True)
#    sell_action_sr=sell_action_sr.sort_index(ascending=True)
#
#    
#    #最大回撤
#    max_retrace=max(list((dy_amount_sr.cummax()-dy_amount_sr)/dy_amount_sr.cummax()))
#    #总盈利
#    total_earnings=dy_amount_sr[-1]-dy_amount_sr[0]
#    #收益率
#    rate_of_return=(dy_amount_sr[-1]-dy_amount_sr[0])/dy_amount_sr[0]
#    #年化收益率
#    years=(dy_amount_sr.index[-1].to_datetime()-dy_amount_sr.index[0].to_datetime()).days/365.0
#    annual_yield=np.power(1+rate_of_return,1.0/years)-1
#    #交易次数
#    num_trade=len(buy_action_sr)
#    #胜率
#    winning_counts=generate_win_counts(buy_action_sr,sell_action_sr)
#    winning_ratio=float(winning_counts)/len(buy_action_sr)
#    #嬴次
#    winning_counts=winning_counts
#    #亏次
#    lose_counts=len(buy_action_sr)-winning_counts
#    
#    x = PrettyTable([u"指标",u"指标值"])
#    x.add_row([u"最大回撤",format(max_retrace,'.2%')])
#    x.add_row([u"总盈利",total_earnings])
#    x.add_row([u"收益率",format(rate_of_return,'.2%')])
#    x.add_row([u"年化收益率",format(annual_yield,'.2%')])
#    x.add_row([u"交易次数",num_trade])
#    x.add_row([u"胜率",format(winning_ratio,'.2%')])
#    #x.add_row([u"嬴次",winning_counts])
#    #x.add_row([u"亏次",lose_counts])
#    print x

#def generate_report(acc):
#    #根据run()的输出生成报告
#    
#    sr=pd.Series(acc.action)
#    sr.index=pd.DatetimeIndex(sr.index)
#  
#    #最大回撤
#    max_retrace=((sr.cummax()-sr)/sr).max()
#    #总盈利
#    total_earnings=sr[-1]-sr[0]
#    #收益率
#    rate_of_return=total_earnings/sr[0]
#    #年化收益率
#    years=(sr.index[-1].to_datetime()-sr.index[0].to_datetime()).days/365.0
#    annual_yield=np.power(1+rate_of_return,1.0/years)-1
#    #交易次数
#    num_trade=len(acc.dead_order)
#    #胜率
#    winning_counts=0
#    for d_order in acc.dead_order:
#        if d_order.profit>0:
#            winning_counts+=1
#    
#    winning_ratio=float(winning_counts)/len(acc.dead_order)
#    #嬴次
#    winning_counts=winning_counts
#    #亏次
#    lose_counts=len(acc.dead_order)-winning_counts
#    
#    x = PrettyTable([u"指标",u"指标值"])
#    x.add_row([u"最大回撤",format(max_retrace,'.2%')])
#    x.add_row([u"总盈利",total_earnings])
#    x.add_row([u"收益率",format(rate_of_return,'.2%')])
#    x.add_row([u"年化收益率",format(annual_yield,'.2%')])
#    x.add_row([u"交易次数",num_trade])
#    x.add_row([u"胜率",format(winning_ratio,'.2%')])
#    x.add_row([u"嬴次",winning_counts])
#    x.add_row([u"亏次",lose_counts])
#    print x
    
    
#codes_list=get_stock_codes(markets=['sz50s'],ipo_date=None)
#
#all_df=fetch_all(codes_list)#,indicators_for_dirverse,diverse_strategy_buy,diverse_strategy_sell)
#all_df=indicators_for_dirverse(all_df)
#all_df=diverse_strategy_buy(all_df)
#all_df=diverse_strategy_sell(all_df)
#acc=test_engine(all_df)
#sr=pd.Series(acc.action)
#sr.index=pd.DatetimeIndex(sr.index)
#sr.plot()
#sr.cummax().plot()



#original_pn=gene_pn(codes_list)
#modified_pn=insert_strategy(original_pn,indicators_for_dirverse,diverse_strategy_buy,diverse_strategy_sell)
#dy_amount_action,buy_action_sr,sell_action_sr=run(modified_pn,12)
##dy_amount_action.plot()
#generate_report(dy_amount_action,buy_action_sr,sell_action_sr)