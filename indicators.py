# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import tushare as ts
# import matplotlib.pyplot as plt
from dateutil.parser import parse
from pandas import DatetimeIndex
import talib







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