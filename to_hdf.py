# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import tushare as ts


def is_stock(df):
    if df['close'].mean()>1000:
        return False
    elif df['close'].mean()<500:
        return True
        
        
def fetch_one(code):
    
    names=['date','time','open','high','low','close','volume','amount']
    years=['2010','2011','2012','2013','2014','2015']
    path_name='/Volumes/ETHANDISK/%s股票五分钟'
    
    df2concat=[]
    
    for year in years:
        for root, dirs, files in os.walk(path_name%year):
            for filename in files:
                if code in filename:
                    path=(path_name%year)+'/'+filename
                    df=pd.read_csv(path,names=names,parse_dates=[[0,1]],infer_datetime_format=True,dtype=np.float64)
                    if is_stock(df):
                        df2concat.append(df)
    try:
        df_total=pd.concat(df2concat)
        df_total['code']=code
    except ValueError:return None
    
    return df_total

def normalize(df):
    
    df=df.set_index('date_time')
    df=df.dropna()
    return df

def fe_all(codes):#:,indi=indicators_for_dirverse,refer1=diverse_strategy_buy,refer2=diverse_strategy_sell):
    
    df_list=[]
    for code in codes:
        try:
            df=fetch_one(code)       
            df=normalize(df)
            df=df.dropna()
            path_name='/Users/xuegeng/WholeData/%s.h5'%code
            df_list.append(df)
            df.to_hdf(path_name,'data',format='fixed')
        except:pass

codes=list(ts.get_today_all().code)
fe_all(codes)
#we=pd.read_hdf('/Users/xuegeng/WholeData/c600000.h5')
