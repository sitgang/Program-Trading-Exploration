# -*- coding: utf-8 -*-
import sys,talib 
reload(sys)
sys.setdefaultencoding('utf-8')
import pymongo,datetime,matplotlib
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt


#BERTREND
UP  = "UP"
DOWN = "DOWN"
DING = "DING"
DI = "DI"
FENXINGDISTANCE = 4#两分型（counter）之间距离大于等于4

class FenxingStra:
    


    def __init__(self):
        
        """===========================规整数据=============================="""
        
        
        ###测试变量
        self.start_time = datetime.datetime(2016,01,05)
        self.end_time = None
        
        ###指标变量
        self.closes = []
        self.macd_len = 34
        self.macd_area_buffer = []#分型出现就清空，添加入backup，macd数据加入areas
        self.macd_area_backup = []#替换不清空
        self.macd_areas = []#第一个分型不去比较红蓝柱子面积
        self.bolling_len = 5
        self.bolling_fenxing = []#布尔值数列，表示分型是否处在超强区域
        self.powerful_area = False#是否在超强区域
        
        self.last_fenxing_datetime = None
        self.last_fenxing_type = None
        
        ###交易变量
        self.trades = []#交易结果
        self.last_fenxing_datetime2 = None
        self.volume = 1
        self.pos = 0
        
        ###绘图变量
        self.fig, self.ax = plt.subplots(figsize = (20,10))
        
        ###分型变量
        self.fenxing = None
        self.lastFenxing = None
        self.fenxingCounter = 0
        self.lastFenxingCounter = 0
        
        ###k线变量
        self.newBar = None
        self.firstBar = None
        self.middleBar = None
        self.lastBar = None
        self.barCounter = 0
        self.barTrend = None#改变为常量
        self.bars = []
        
        ###包含变量
        self.hasBaohan = False
        
        ###统计变量
        self.dingfenxingTuples = []
        self.difenxingTuples = []
        self.fenxingTuples = []
        self.dingfenxingTimes = []
        self.dingfenxingPrices = []
        self.difenxingTimes = []
        self.difenxingPrices = []
        
        ###数据变量
        self.df = self.prepare_df()
        self.barGenerator = self.iterbar()
        self.prepare_indextool()

    def prepare_df(self):
        
        """===========================准备数据=============================="""
        
        dbClient = pymongo.MongoClient()
        collection = dbClient["VnTrader_1Min_Db"]["RB0000"]
        self.df =pd.DataFrame(list(collection.find({'datetime':{'$gte':self.start_time}})))
        df = self.df.drop_duplicates()
        del df['_id']
        df['datetime'] = df['datetime'].map(lambda x:x-datetime.timedelta(days = 1) if x.hour > 19 else x)#期货数据的特殊性，比如20号21点的数据是存储为21号21点的，我们把它处理成20号的
        df = df.sort_values('datetime')
        index = pd.Index(np.arange(df.count()[0]))
        df.index = index 
        df[['open','close','low','high']] = df[['open','close','low','high']].applymap(float)
        df[['volume']] = df[['volume']].applymap(int)
        return df
    
    def prepare_indextool(self):
        
        """===========================准备指标用的数据=============================="""
        dbClient = pymongo.MongoClient()
        collection = dbClient["VnTrader_1Min_Db"]["RB0000"]
        query = {'datetime':{'$gte':self.start_time-datetime.timedelta(days = 1),'$lt':self.start_time}}
        df = pd.DataFrame(list(collection.find(query)))
        df = df.drop_duplicates()
        del df['_id']
        df['datetime'] = df['datetime'].map(lambda x:x-datetime.timedelta(days = 1) if x.hour > 19 else x)#期货数据的特殊性，比如20号21点的数据是存储为21号21点的，我们把它处理成20号的
        df = df.sort_values('datetime')
        index = pd.Index(np.arange(df.count()[0]))
        df.index = index 
        df[['open','close','low','high']] = df[['open','close','low','high']].applymap(float)
        df[['volume']] = df[['volume']].applymap(int)
        
        self.closes.extend(list(df[-self.macd_len:].close))#准备好计算指标用的收盘价
        
        #充入三个预备数据
        self.firstBar = df.ix[df.count()[0]-3]
        self.middleBar = df.ix[df.count()[0]-2]
        self.lastBar = df.ix[df.count()[0]-1]
    
    def iterbar(self):
        
        """===========================K线生成器函数=============================="""
        
        for row in self.df.iterrows():
            yield row[1]
        
    
    
    def process_baohan(self):
        """===========================包含函数=================================="""

        """
        存在包含条件的k线进行包含处理
        """
        if self.lastFenxing and self.newBar['low'] >= self.lastBar['low'] and self.newBar['high'] <= self.lastBar['high']:#存在包含关系;分型之后才需要判断包含
                
            self.hasBaohan = True
            #self.newBar = None #这根K线被包含了，不算
        
        else:
            self.hasBaohan = False
            self.firstBar = self.middleBar
            self.middleBar = self.lastBar
            self.lastBar = self.newBar
            self.barCounter += 1
            self.bars.append(self.newBar)
            #self.newBar = None
        
    
    def process_fenxing(self):
        """===========================分型函数=============================="""
        """
        用于确定顶分型和底分型
        """
        
        #顶分型
        if (self.middleBar['high'] > self.firstBar['high'] and self.middleBar['high'] > self.lastBar['high']
            and self.middleBar['low'] > self.firstBar['low'] and self.middleBar['low'] > self.firstBar['low']):
            self.fenxing = (self.middleBar['datetime'],self.middleBar['high'],DING)
            self.fenxingCounter = self.barCounter
            
            try:#如果上个分型不存在，直接加入分型队列
                assert self.lastFenxing
            except AssertionError:
                self.fenxingTuples.append(self.fenxing)
                self.lastFenxing = self.fenxing
                self.lastFenxingCounter = self.fenxingCounter
            
            if self.lastFenxing[2] == DING:#如果上一个分型也是顶分型的话，保留高的那个
                if self.fenxing[1] >= self.lastFenxing[1]:#如果后来居上
                    self.fenxingTuples[-1] = self.fenxing
                    self.lastFenxing = self.fenxing
                    self.lastFenxingCounter = self.fenxingCounter
                else:#后者顶分型力度不够
                    pass
                    
            else:#上一个分型是底分型,无共用K线，就加入列表，确认分型
                if self.fenxingCounter - self.lastFenxingCounter >= FENXINGDISTANCE :#无共用k线
                    self.fenxingTuples.append(self.fenxing)
                    self.lastFenxing = self.fenxing
                    self.lastFenxingCounter = self.fenxingCounter
            
        #底分型
        elif (self.middleBar['high'] < self.firstBar['high'] and self.middleBar['high'] < self.lastBar['high']
            and self.middleBar['low'] < self.firstBar['low'] and self.middleBar['low'] < self.firstBar['low']):
            
            self.fenxing = (self.middleBar['datetime'],self.middleBar['low'],DI)
            self.fenxingCounter = self.barCounter
            
            try:#如果上个分型不存在，直接加入分型队列
                assert self.lastFenxing
            except AssertionError:
                self.fenxingTuples.append(self.fenxing)
                self.lastFenxing = self.fenxing
                self.lastFenxingCounter = self.fenxingCounter
            
            
            if self.lastFenxing[2] == DI:#如果上一个分型也是底分型的话，保留低的那个
                
                if self.fenxing[1] <= self.lastFenxing[1]:#如果后来居下
                    self.fenxingTuples[-1] = self.fenxing
                    self.lastFenxing = self.fenxing
                    self.lastFenxingCounter = self.fenxingCounter
                
                else:#后者底分型力度不够
                    pass
            else:#上一个分型是顶分型,无共用K线，就加入列表，确认分型
                if self.fenxingCounter - self.lastFenxingCounter >= FENXINGDISTANCE :#无共用k线
                    self.fenxingTuples.append(self.fenxing)
                    self.lastFenxing = self.fenxing
                    self.lastFenxingCounter = self.fenxingCounter
        #无分型
        else:
            pass
        
    
    def process_indextools(self):
        
        """======================更新辅助指标=================="""
        
        ###更新closes
        close = self.newBar['close']
        self.closes.append(close)
        if len(self.fenxingTuples)<=1:return
        now_fenxing = self.fenxingTuples[-1]
        ###判断分型是否更新
        ###未更新
        if self.last_fenxing_datetime == now_fenxing[0]:
            
            self.macd_area_buffer.append(talib.MACD(np.array(self.closes))[-1][-1])#buffer添加一个
            
            
        ###更新了
        else:
            ###替代前分型
            if self.last_fenxing_type == now_fenxing[2]:
                
                #macd处理
                self.macd_area_buffer.append(talib.MACD(np.array(self.closes))[-1][-1])#buffer添加一个
                self.macd_area_backup.extend(self.macd_area_buffer)#backup加入buffer
                macd_area = sum(self.macd_area_backup)#计算
                #self.macd_areas[-1] = macd_area#替换最后一个红蓝柱面积
                self.macd_areas[-1] = (now_fenxing[0],macd_area)#替换最后一个红蓝柱面积
                self.macd_area_buffer = []#清空buffer
                
                #bolling处理
                ceil = talib.BBANDS(np.array(self.closes))[0][-1]
                floor = talib.BBANDS(np.array(self.closes))[-1][-1]
                self.powerful_area = ((now_fenxing[1] > ceil) | (now_fenxing[1] < floor))
                #self.bolling_fenxing[-1] = self.powerful_area
                self.bolling_fenxing[-1] = (now_fenxing[0],self.powerful_area)
                
                #判断变量
                self.last_fenxing_datetime = now_fenxing[0]
                
            ###增加新的分型    
            else:
                
                #macd处理
                self.macd_area_backup = []#清空backup
                self.macd_area_buffer.append(talib.MACD(np.array(self.closes))[-1][-1])#buffer添加一个
                self.macd_area_backup.extend(self.macd_area_buffer)#backup加入buffer
                macd_area = sum(self.macd_area_backup)
                #self.macd_areas.append(sum(self.macd_area_backup))#增加一个红蓝柱面积
                self.macd_areas.append((now_fenxing[0],macd_area))#增加一个红蓝柱面积
                self.macd_area_buffer = []#清空buffer
                
                #bolling处理
                ceil = talib.BBANDS(np.array(self.closes))[0][-1]
                floor = talib.BBANDS(np.array(self.closes))[-1][-1]
                self.powerful_area = ((now_fenxing[1] > ceil) | (now_fenxing[1] < floor))
                #self.bolling_fenxing.append(self.powerful_area)
                self.bolling_fenxing.append((now_fenxing[0],self.powerful_area))
                
                #判断变量
                self.last_fenxing_datetime = now_fenxing[0]
                self.last_fenxing_type = now_fenxing[2]
    
    def process_tradesignal(self):
        
        """======================发出交易指令=================="""
        
        #至少第六个分型才能比较指标，因为这个策略是第二买卖点策略
        if len(self.fenxingTuples) < 7:return 
        now_fenxing = self.fenxingTuples[-1]
        
        ###判断分型是否更新
        ###未更新
        if self.last_fenxing_datetime2 == now_fenxing[0]:
            return
            
        ###更新了
        else:
            ###不管替代前分型还是新增分型,满足条件的话，变一次买一次
            first_sell_macd = self.macd_areas[-3][-1]
            qian_fenxing_macd = self.macd_areas[-5][-1]
            macd_beichi = abs(first_sell_macd) < abs(qian_fenxing_macd)
            first_sell_bolling = self.bolling_fenxing[-3][-1]
            qian_fenxing_bolling = self.bolling_fenxing[-5][-1]
            bolling_beichi = (not first_sell_bolling) and qian_fenxing_bolling
            
            #对于这个分型是否是第二卖点的判断
            if now_fenxing[-1] == DING:
                first_sell_point = self.fenxingTuples[-3]
                qianding = self.fenxingTuples[-5]
                new_high = first_sell_point[1] > qianding[1]#创出新高
                if new_high and (macd_beichi or bolling_beichi):
                    
                    self.trades.append((self.newBar['datetime'],self.newBar['close']-1,self.volume,"SELL")) 
                    
                    
            #对于这个分型是否是第二买点的判断
            elif now_fenxing[-1] == DI:
                first_sell_point = self.fenxingTuples[-3]
                qiandi = self.fenxingTuples[-5]
                new_high = first_sell_point[1] < qiandi[1]#创出新低
                if new_high and (macd_beichi or bolling_beichi):
                    self.trades.append((self.newBar['datetime'],self.newBar['close']+1,"BUY"))
                            
            self.last_fenxing_datetime2 = now_fenxing[0]     
                
    def calculate_result(self):
        
        buy = []
        short = []
        
        much = 0
        max_zhanyong = 0#最大资金占用
        max_zhanyong_tmp = 0
        
        for i in self.trades:
            price = i[1]
            if i[2] == "BUY":
                
                if short:
                    for c1,sellPrice in enumerate(short):
                        volume = c1+1
                        #if volume > 5:break
                        much += (sellPrice-price-1)*(volume)
                        max_zhanyong_tmp += sellPrice*(volume)*0.6
                   
                    short = []
                    max_zhanyong = max(max_zhanyong,max_zhanyong_tmp)
                    max_zhanyong_tmp = 0
                
                buy.append(i[1])
                
            else:
                
                if buy:
                    for c2,buyPrice in enumerate(buy):
                        volume = c2+1
                        #if volume > 5:break
                        much += (price-buyPrice-1)*(volume)
                        max_zhanyong_tmp += sellPrice*(volume)*0.6
                        
                    buy = []
                    max_zhanyong = max(max_zhanyong,max_zhanyong_tmp)
                    max_zhanyong_tmp = 0
                
                short.append(i[1])
            
        pnl =  much*10#一个点十块钱
        print "PROFIT " + str(pnl)
        print "MAX OCCUPIED " + str(max_zhanyong)

            
                
                        
    def run(self):
        
        """===========================测试函数=============================="""
        
        while True:
            
            try:
                self.newBar = self.barGenerator.next()
            except StopIteration:
                return
            self.process_baohan()
            self.process_fenxing()
            self.process_indextools()
            self.process_tradesignal()
            self.newBar = None
    
            #print len(self.fenxingTuples)


    def draw_candlestick(self):
        
        """===========================绘图函数=============================="""
        
        quotes=self.df[['datetime','open','high','low','close']].values
        tuples = [tuple(x) for x in quotes]
        qw=[]
            
        for things in tuples:
            date=matplotlib.dates.date2num(things[0])
            tuple1=(date,things[1],things[2],things[3],things[4])
            qw.append(tuple1)
        
        self.ax.xaxis_date()
        self.ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%y-%m-%d\n%H:%M:%S'))
        plt.xticks(rotation=45)
        
        self.ax.grid(linestyle='-', linewidth=0.1)
        matplotlib.finance.candlestick_ohlc(self.ax, qw, colorup='r',colordown='g', alpha =.4, width=0.0005)
        self.fig.show()

    def drawdingdi(self):
        
        try:
            self.run()
        except StopIteration:
            pass    
        
        for fx in self.fenxingTuples:
            if fx[2] == DI:
                self.difenxingTuples.append(fx)
            elif fx[2] == DING:
                self.dingfenxingTuples.append(fx)
        
            
        self.dingfenxingTimes = [i[0] for i in self.dingfenxingTuples]
        self.dingfenxingPrices = [i[1] for i in self.dingfenxingTuples]
        self.difenxingTimes = [i[0] for i in self.difenxingTuples]
        self.difenxingPrices = [i[1] for i in self.difenxingTuples]
        
        self.draw_candlestick()
        self.ax.scatter(self.difenxingTimes,self.difenxingPrices,marker='^',c='r',s=60)
        self.ax.scatter(self.dingfenxingTimes,self.dingfenxingPrices,marker='v',c='g',s=60)
        self.fig.show()
    






#fenxingS.drawdingdi()

s = FenxingStra()










