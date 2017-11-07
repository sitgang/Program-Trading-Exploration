# -*- coding: utf-8 -*-
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
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
    
    freq_barwidth_dict = {'D':0.5,'d':0.5,'1min':0.0005,'1Min':0.0005}
    
    for things in tuples:
        date=matplotlib.dates.date2num(things[0])
        tuple1=(date,things[1],things[2],things[3],things[4])
        qw.append(tuple1)
    
    fig, ax = plt.subplots()
    
    ax.xaxis_date()
    ax.grid(linestyle='-', linewidth=0.1)
    matplotlib.finance.candlestick_ohlc(ax, qw, colorup='r',\
        colordown='g', alpha =.4, width=freq_barwidth_dict[freq])
  
    
#df = pd.read_hdf('/Users/xuegeng/Desktop/df.h5')

def tearDF(df):
    """
    tear df apart
    return a list of df
    """
    retDFs = []
    try:
        symbolArray = np.unique(list(df['symbol']))
    except:
        return retDFs
    
    for symbol in symbolArray:
        retDFs.append(df[df['symbol'] == symbol].copy())
    return retDFs

    
def resample(df,freq='B'):
    '''
    freq:str    "B" for business day
                "W" for week
                "T for minite"
                "H" for hour
    =================================
    return : DataFrame resampled
    '''
    
    if not isinstance(df.index,pd.DatetimeIndex):
        df = df.set_index('datetime')
    df.index=pd.DatetimeIndex(df.index)
    df=df.sort_index(ascending=False)
    
    ls=[df[['open']].resample(freq).first(),
        df[['high']].resample(freq).max(),
        df[['low']].resample(freq).min(),
        df[['close']].resample(freq).last()]
    
    mature_df=pd.concat(ls,axis=1)
    mature_df['symbol']=str(df['symbol'][0])
    df=mature_df.dropna()
    
    return df