# -*- coding: utf-8 -*-
import pandas as pd
#pd.options.display.max_rows=10


from OrderAccount import Account,Order


from indicators import indicators_for_dirverse,indicators_for_crosses


from strategy import diverse_strategy_buy,diverse_strategy_sell,golden_cross,dead_cross


from colle_tool import mailhelper,save_report,toround,draw_candlestick


from data_fetcher import fetch_all,fetch_one,get_stock_codes,normalize


from testtest import test_engine


#from sifter import SifterAll,SifterOne


import sys
reload(sys)
sys.setdefaultencoding('utf-8')