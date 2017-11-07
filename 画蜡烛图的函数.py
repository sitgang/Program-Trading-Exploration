# -*- coding: utf-8 -*-
import matplotlib
import matplotlib.pyplot as plt
from indicators import indicators_for_dirverse,indicators_for_crosses
from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross



def draw_candlestick(df):#df已被规范化，时间序列的ohlcva

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
    
    fig, ax = plt.subplots()
    
    ax.xaxis_date()
    ax.grid(linestyle='-', linewidth=0.2)
    matplotlib.finance.candlestick_ohlc(ax, qw, width=.5, colorup='r',colordown='g', alpha =.4)


def individual_demo(df,i=indicators_for_dirverse,
                    b=diverse_strategy_buy,
                    s=diverse_strategy_sell):

    df=indicators_for_dirverse(df)
    df=diverse_strategy_buy(df)
    df=diverse_strategy_sell(df)
    dfs=df[df['sell_signal']]
    dfb=df[df['buy_signal']]
    draw_candlestick(df)
    plt.scatter(dfs.index,dfs.low,marker='v',c='g',s=60)
    plt.scatter(dfb.index,dfb.high,marker='^',c='r',s=60)    