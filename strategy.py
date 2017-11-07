# -*- coding: utf-8 -*-
import os
import pandas as pd
pd.options.display.max_rows=10
import numpy as np
from indicators import indicators_for_dirverse,indicators_for_crosses


from dateutil.parser import parse
import talib
import sys
from scipy import interpolate
from datetime import datetime
reload(sys)
sys.setdefaultencoding('utf-8') 


CLOSE_SAMPLE=[ 24.76,  24.28,  25.21,  26.25,  28.88,  28.99,  28.35,  31.19,34.31,  36.49,  35.67,  32.1 ,  32.18,  31.7 ,  30.8 ,  30.77,29.77,  27.7 ,  28.76]
LOW_SAMPLE=[ 24.2 ,  24.01,  23.41,  24.  ,  26.37,  27.25,  27.4 ,  31.19,33.4 ,  33.4 ,  35.08,  32.1 ,  30.7 ,  31.01,  30.27,  30.5 ,29.45,  27.6 ,  27.7 ]
GBKM_SAMPLE=[ 75.27683505,  74.16337925,  74.90652869,  77.40264178,81.75542302,  86.66794839,  88.29240889,  86.10675256,84.7067632 ,  87.00756837,  90.50308921,  89.76234594,82.57561793,  71.43528003,  59.91510841,  50.53179488,43.08981872,  36.17388661,  29.83802615]

CLOSE_SAMPLE2=[ 20.33,  21.05,  21.49,  20.29,  22.32,  24.55,  27.01,  29.71,32.68,  31.77,  34.95,  38.45,  42.3 ,  46.53,  51.18,  50.  ,47.5 ,  48.  ,  47.  ,  42.41,  43.68,  48.05]
LOW_SAMPLE2=[ 19.99,  20.25,  20.68,  20.29,  19.78,  22.81,  25.  ,  28.36,30.45,  30.7 ,  31.18,  35.52,  41.1 ,  46.53,  47.65,  46.63,45.5 ,  46.  ,  45.5 ,  42.3 ,  41.5 ,  43.18]
GBKM_SAMPLE2=[ 93.71592611,  91.21636003,  87.46623061,  83.41955066,80.66983087,  81.01571395,  84.73545107,  90.40899863,95.05322187,  96.89845728,  96.5647677 ,  95.76976925,96.00042368,  97.37205819,  98.6860291 ,  99.1305236 ,98.05462598,  94.43946125,  88.22010362,  79.89313723,70.47144951,  62.78129296]



def indicators_for_dirverse(df):

	df=df.dropna()
	df=df.sort_index()
	df['MACD'],df['MACD_signal'],df['MACD_hist']=talib.MACD(np.array(df['close']))
	df['var1']=(2*df['close']+df['high']+df['low']+df['open'])/5.0
	df['var2']=talib.MIN(np.array(df['low']),timeperiod=34)
	df['var3']=talib.MAX(np.array(df['low']),timeperiod=34)
	df['buffer']=(df['var1']-df['var2'])/(df['var3']-df['var2'])*100
	df['SK']=talib.EMA(np.array(df['buffer']),timeperiod=13)
	df['SD']=talib.EMA(np.array(df['SK']),timeperiod=3)
	df['MACD_MIN']=talib.MIN(np.array(df['MACD']),timeperiod=9)
	df['PRICE_MIN']=talib.MIN(np.array(df.close),9)
	df['PRICE_MAX']=talib.MAX(np.array(df.close),9)
	df['RSI'] = talib.RSI(np.array(df.close))
    
	df=df.sort_index(ascending=False)
	df=df.dropna()
	return df


def indicators_for_crosses(df):
    
    df=df.dropna()
    df=df.sort_index()
    df['MA5']=talib.MA(np.array(df['close']),5)
    df['MA10']=talib.MA(np.array(df['close']),10)
    df['MA20']=talib.MA(np.array(df['close']),20)
    df['LONG_ARR']=(df['MA5']>df['MA10'])&(df['MA10']>df['MA20'])
    df['SHORT_ARR']=(df['MA5']<df['MA10'])&(df['MA10']<df['MA20'])
    df['PRICE_MAX']=talib.MAX(np.array(df.close),3)
        
    df=df.sort_index(ascending=False)
    df=df.dropna()
    return df
    
    
def diverse_strategy_buy(df): #策略
    '''
    PRICE_MIN_9,MACD,MIN_MACD
    '''
    df['price_gorge']=df['PRICE_MIN']!=df['PRICE_MIN'].shift(-1)
    df['MACD_gorge']=df['MACD']>df['MACD_MIN'].shift(-1)
    df['SDSKlt20']=(df['SK']<20)&(df['SD']<20)
    df['buy_signal']=df['SDSKlt20']&df['MACD_gorge']&df['price_gorge']
    df=df.dropna()
    return df

def diverse_strategy_sell(df):
    '''背离'''
    df['price_peak']=df['PRICE_MAX']!=df['PRICE_MAX'].shift(-1)
    df['MACD_peak']=df['MACD']>df['MACD_MIN'].shift(-1)
    df['SDSKgt80']=(df['SK']>80)&(df['SD']>80)
    #df['quick_sell']=(df['ma5']<df['ma20'])&(df['ma5'].shift(-1)>df['ma20'].shift(-1))
    #df['LossLimit']=df['close']<df['PRICE_MAX']*0.92
    df['sell_signal']=(df['SDSKgt80']&df['MACD_peak']&df['price_peak'])#|df['LossLimit']#|df['quick_sell']
    df=df.dropna()
    return df

def golden_cross(df):
    
    df=indicators_for_crosses(df)
    df['buy_signal']=df['LONG_ARR']&(df['SHORT_ARR'].shift(-4))
    df=df.dropna()
    
    return df

def dead_cross(df):
   
    df=indicators_for_crosses(df)
    df['sell_signal']=df['SHORT_ARR']&(df['LONG_ARR'].shift(-4)) 
    df=df.dropna()
    
    return df    
    
def return_similarity(va,vb,ignore_start=True):
    '''regardless of where you start'''
    va=np.array(va)    
    vb=np.array(vb)
    
    lena=len(va)
    lenb=len(vb)
        
    if lena!=lenb:    
        if lena>lenb:        
            sarr=vb
            larr=va
        if lena<lenb:
            sarr=va
            larr=vb
        
        xs=np.array(np.linspace(1,len(sarr),len(sarr)))
        xl=np.array(np.linspace(1,len(sarr),len(larr)))        
        f = interpolate.interp1d(xs, sarr)
        va = f(xl)
        vb = larr
    if ignore_start:    
        va=va-va[0]
        vb=vb-vb[0]
    
    num=float(va.T.dot(vb))    
    denom=np.linalg.norm(va)*np.linalg.norm(vb)    
    an_cos=num/denom    
    an_sin=0.5+0.5*an_cos
    
    #越接近1，相似度越高
    
    return an_sin



def rs(arr,*args,**kwargs):
    arr=list(arr)
    results=[]
    for sample in args:
        
        results.append(return_similarity(arr,sample,ignore_start=True))
       
    result=np.mean(results)
    
    return result
def rs2(arr,*args,**kwargs):
    arr=list(arr)
    results=[]
    for sample in args:
        
        results.append(return_similarity(arr,sample,ignore_start=False))
       
    result=np.mean(results)
    
    return result
def stra_simi(df,idx,ignore_start=True,*args,**kwargs):
    
    '''
    idx:column name youwant to compare with
    args should be passed into samples of list or array type
    kwargs' keys got 'name'...
    '''
    
    if not args:
        return
    
    bucket=[]
    for sample in args:
        bucket.append(df[idx].rolling(center=False,window=len(sample)).apply(func=rs,args=args))
    srs=pd.concat(bucket,axis=1)
    if kwargs:
        df[kwargs['name']]=srs.apply(np.mean,axis=1)
    else:
        df['Similarity']=srs.apply(np.mean,axis=1)
    
    df=df.sort_index()
    df=df.dropna()
    return df
def stra_simi2(df,idx,ignore_start=True,*args,**kwargs):
    
    '''
    idx:column name youwant to compare with
    args should be passed into samples of list or array type
    kwargs' keys got 'name'...
    '''
    
    if not args:
        return
    
    bucket=[]
    for sample in args:
        bucket.append(df[idx].rolling(center=False,window=len(sample)).apply(func=rs2,args=args))
    srs=pd.concat(bucket,axis=1)
    if kwargs:
        df[kwargs['name']]=srs.apply(np.mean,axis=1)
    else:
        df['Similarity']=srs.apply(np.mean,axis=1)
    
    df=df.sort_index()
    df=df.dropna()
    return df   
    
    
def indi_GBKM(df):
    '''GBKM1 is slower than GBKM'''
    
    
    def t(sd):
        if sd==0:return 0.000001
        else:return sd

    df['var4']=(df.close-talib.MIN(np.array(df.low),22))/np.array(map(t,(talib.MAX(np.array(df.high),22)-talib.MIN(np.array(df.low),22))))*100
    df['var5']=(df.close-talib.MIN(np.array(df.low),10))/np.array(map(t,(talib.MAX(np.array(df.high),10)-talib.MIN(np.array(df.low),10))))*100
    df['var6']=(df.close-talib.MIN(np.array(df.low),5))/np.array(map(t,(talib.MAX(np.array(df.high),5)-talib.MIN(np.array(df.low),5))))*100
    df['var7']=talib.EMA(talib.SMA(np.array(df['var4']+df['var5']+df['var6'])/3,2),3)
    df['GBKM']=talib.SMA(np.array(df['var7']),3)
    df['GBKM1']=talib.SMA(np.array(df['GBKM']),2)

    
    df=df.sort_index()
    df=df.dropna()
    return df


def div_gbkm(df):
    
    df=indi_GBKM(df)
    
    '''sample=np.array(dft[(dft.index>start)&(dft.index<end)&()dft.code==code])'''

    close_sample=[ 24.76,  24.28,  25.21,  26.25,  28.88,  28.99,  28.35,  31.19,34.31,  36.49,  35.67,  32.1 ,  32.18,  31.7 ,  30.8 ,  30.77,29.77,  27.7 ,  28.76]
    low_sample=[ 24.2 ,  24.01,  23.41,  24.  ,  26.37,  27.25,  27.4 ,  31.19,33.4 ,  33.4 ,  35.08,  32.1 ,  30.7 ,  31.01,  30.27,  30.5 ,29.45,  27.6 ,  27.7 ]
    gbkm_sample=[ 75.27683505,  74.16337925,  74.90652869,  77.40264178,81.75542302,  86.66794839,  88.29240889,  86.10675256,84.7067632 ,  87.00756837,  90.50308921,  89.76234594,82.57561793,  71.43528003,  59.91510841,  50.53179488,43.08981872,  36.17388661,  29.83802615]

    close_sample2=[ 20.33,  21.05,  21.49,  20.29,  22.32,  24.55,  27.01,  29.71,32.68,  31.77,  34.95,  38.45,  42.3 ,  46.53,  51.18,  50.  ,47.5 ,  48.  ,  47.  ,  42.41,  43.68,  48.05]
    low_sample2=[ 19.99,  20.25,  20.68,  20.29,  19.78,  22.81,  25.  ,  28.36,30.45,  30.7 ,  31.18,  35.52,  41.1 ,  46.53,  47.65,  46.63,45.5 ,  46.  ,  45.5 ,  42.3 ,  41.5 ,  43.18]
    gbkm_sample2=[ 93.71592611,  91.21636003,  87.46623061,  83.41955066,80.66983087,  81.01571395,  84.73545107,  90.40899863,95.05322187,  96.89845728,  96.5647677 ,  95.76976925,96.00042368,  97.37205819,  98.6860291 ,  99.1305236 ,98.05462598,  94.43946125,  88.22010362,  79.89313723,70.47144951,  62.78129296]

    df=stra_simi(df,'close',close_sample,close_sample2,name='close_simi')
    df=stra_simi(df,'low',low_sample,low_sample2,name='low_simi')
    df=stra_simi2(df,'GBKM1',gbkm_sample,gbkm_sample2,name='gbkm_simi')
    
    df['decisive']=(df['low_simi']+df['close_simi']+df['gbkm_simi'])/3
    df['buy_signal']=(df.decisive>0.990)#&(df['SK']<40)
    
    df=df.dropna()
    df=df.sort_index()
    
    return df










