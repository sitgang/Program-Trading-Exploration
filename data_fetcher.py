# -*- coding: utf-8 -*-
import pandas as pd
pd.options.display.max_rows=40
import tushare as ts
import numpy as np
#from indicators import indicators_for_dirverse,indicators_for_crosses
#from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross,dead_cross
from dateutil.parser import parse
import shelve
from multiprocessing.dummy import Pool





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
    if 'all' in markets:#所有 
        f=shelve.open('/Users/xuegeng/allcodes.xg')
        codes=f['codes']
        f.close()
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
    
    c=[]
    for code in desired_codes:
        try:
            code=int(code)
        except ValueError:
            continue
        if len(str(code))==6:c.append(str(code))
        if len(str(code))==5:c.append('0'+str(code))
        if len(str(code))==4:c.append('00'+str(code))
        if len(str(code))==3:c.append('000'+str(code))
        if len(str(code))==2:c.append('0000'+str(code))
        if len(str(code))==1:c.append('00000'+str(code))
        
    
    return c

def fetch_one(code):
    try:
        df=pd.read_hdf('/Volumes/ETHAN/WholeData/%s.h5'%code)
        df['code']=code
        return df
    except IOError:
        print "We don't have %s's data"%code

def gall(codes):
    p=Pool(4)
    result=p.map(fetch_one,codes)
    p.close()
    p.join()
    return result



#对df进行一些标准化处理
def normalize(df,freq='B'):
    '''freq:str  "B" for business day
                 "W" for week
                 "T for minite"
                 "H" for hour
    ==================================
    return : DataFrame normalized'''
    
    df.index=pd.DatetimeIndex(df.index)
    
    df=df.sort_index(ascending=False)
    ls=[df[['open']].resample(freq).first(),
    df[['high']].resample(freq).max(),
    df[['low']].resample(freq).min(),
    df[['close']].resample(freq).last()]
    
    mature_df=pd.concat(ls,axis=1)
    mature_df['code']=str(df.code[0])
    
    df=mature_df.dropna()
    return df
    
    
def fetch_all(codes,
                freq='B',
                indi=None,#indicators_for_dirverse,
                refer1=None,#diverse_strategy_buy,
                refer2=None,#diverse_strategy_sell
                ):
    
    df_list=[]
    
    if isinstance(codes,str):
        codes=[codes]

    for code in codes:
        
        df=fetch_one(code)
        try: 
            df=normalize(df,freq=freq)
        except AttributeError:
            continue
       
        
        df=df.dropna()
        if indi:
            if len(indi)>1:
                for ind in indi:
                    df=ind(df)
            else:df=indi[0](df)
        if refer1:
            df=refer1(df)
        if refer2:
            df=refer2(df)
            
        df_list.append(df)
    
    df_all=pd.concat(df_list)
    
    return df_all