# -*- coding: utf-8 -*-
from multiprocessing.dummy import Pool
import tushare as ts
from data_fetcher import get_stock_codes
from time import time
from indicators import indicators_for_crosses
from strategy import golden_cross

def testst(df):
    df['buy_signal']=df['close']>df['open'] 
    return df

def sifter(markets,stra,ktype):
    '''过滤得到符合策略的股票'''
    def get_hist_data(code):
        df=ts.get_hist_data(code,ktype=ktype)
        df['code']=code
        return df
    def sif(df):
        try:
            df=df.sort_index()
            df=stra(df)
            df=df.dropna()
            row=df.iloc[-1]
            signal=row['buy_signal']
            if signal==True:
                return df['code'][0]
            else:
                return (df.iloc[-1])['buy_signal']
            
        except:
            return None
        
        
    codes=get_stock_codes(markets)
    
    pool=Pool(19)
    result=pool.map(get_hist_data,codes)
    pool.close()
    pool.join()
    
    chosen=[]
    for df in result:
        chosen.append(sif(df))
        
    chosen=list(set(chosen))
    if False in chosen:
        chosen.remove(False)
    if None in chosen:
        chosen.remove(None)

    f=open('/Users/xuegeng/Desktop/zshingen_right/todayselection.txt','w')
    f.write(str(chosen))
    f.close()
    
    
