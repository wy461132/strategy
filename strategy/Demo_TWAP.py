import datetime
import time

import ctaEngine
import numpy as np
from ctaBase import *
from ctaTemplate import *


class Demo_TWAP(CtaTemplate):
    """仅供测试_标准TWAP算法"""
    vtSymbol = ''
    exchange = ''
    className = 'Demo_TWAP'
    author = 'ljt'
    name = EMPTY_UNICODE # 策略实例名称

    # 参数映射表
    paramMap = {
        'exchange': '交易所',
        'vtSymbol': '合约',
        'init_time': '算法总时长(秒)',
        'sids': '价格检查间隔',
        'offset': '交易方向',
        'type': '开平',
        'max_volume': '单笔上限数量',
        'min_volume': '单笔下限数量',
        'volume': '委托总手数'
    }
    # 参数列表，保存了参数的名称
    paramList = list(paramMap.keys())

    # 变量映射表
    varMap = {
        'trading': '交易中',
        'pos': '净持仓位',
        'volume_per': '单笔委托量',
        'Time_per': '单笔执行时间'
    }
    # 变量列表，保存了变量的名称
    varList = list(varMap.keys())

    def __init__(self, ctaEngine=None, setting={}):
        super().__init__(ctaEngine, setting)
        self.volume_per = []
        self.Time_per = 0
        self.init_time = 100
        self.sids = 10
        self.offset = 'buy'
        self.type = 'open'
        self.max_volume = 20
        self.min_volume = 10
        self.volume = 0 # 委托总手数
        self.m = 0 # 单笔报单数量
        self.number = 0 # 报单次数
        self.t = 0 # 报单时间间隔
        self.sig = True
        self.sigg = 0 # 报单参数控制
        self.siggg = 0 #报单是否全部成交
        self.askprice = 0
        self.bidprice = 0
        self.ordertime_one = [] #首笔报单时间
        self.ordertime_two = '' #撤单后报单时间
        self.v = 0
        self.id = ''
        self.j = 1 # 首次报单次数控制
        self.k = 0  # 报单次数控制
        self.vv = 0 # 部分成交量
        self.a = 0
        self.orderprice = 0
        self.gogogo = 0 # fak在追单控制


    def onTick(self, tick):
        super().onTick(tick)
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return
        self.askprice = tick.askPrice1
        self.bidprice = tick.bidPrice1
        if self.sig and self.sigg == 0 and self.askprice != 0 and self.bidprice != 0:
            self.send(self.offset, self.type, self.volume_per[0],
                      self.bidprice if self.offset == 'buy' else self.askprice)
            self.sigg = 1
            self.ordertime_one.append(datetime.datetime.now())
            self.ordertime_two = self.ordertime_one[0] + datetime.timedelta(seconds=self.sids)
            for i in range(1, self.number + 1):
                self.ordertime_one.append(self.ordertime_one[0] + datetime.timedelta(seconds=i * self.Time_per))


    def onTrade(self, trade):
        super().onTrade(trade, log=True)


    def onOrder(self, order, log=False):
        if order.status == '未成交' or order.status == '部分成交' or order.status == '部成部撤':
            self.id = order.orderID
            self.vv = order.totalVolume - order.tradedVolume
            self.orderprice = order.price
        elif order.status == '全部成交' and order.orderID == self.id:
            self.id = 0
            self.vv = 0


    def onStart(self):
        self.manage_position()
        self.volume_per.append(np.random.randint(low=self.min_volume, high=self.max_volume,))
        while self.volume - sum(self.volume_per) > self.max_volume:
            self.volume_per.append(np.random.randint(low=self.min_volume, high=self.max_volume,))
        self.volume_per.append(self.volume - sum(self.volume_per))
        self.output(self.volume_per)
        self.number = len(self.volume_per)
        self.Time_per = round(self.init_time / self.number)
        self.output(self.Time_per)
        if self.Time_per < 1:
            self.sig = False
            self.ouput('参数异常导致报单时间间隔过短，需重新修改参数')
        super().onStart()
        self.output(datetime.datetime.now())
        self.regTimer(22, 500)

    # 本地时间定时判断
    def onTimer(self, tid):
        super().onTimer(tid)
        now_time = datetime.datetime.now()
        if tid == 22:
            for i in range(0, self.number - 1):
                ctaEngine.writeLog(f'{len(self.ordertime_one)}, {i+1}, {self.ordertime_one}')
                if now_time >= self.ordertime_one[i+1] and self.j == i+1 and self.Time_per >= self.sids:
                    if self.id != '':
                        self.cancelOrder(self.id)  #撤单要判断撤单是否成功，否者这里会出现重复发单
                        time.sleep(0.1)
                        if self.vv != 0:
                            self.sendfak(self.offset, self.type, self.vv,
                                      self.askprice + 10 if self.offset == 'buy' else self.bidprice - 10) #直接对手价超价10报单，不成交这里会导致数量缺失
                            self.gogogo = 1
                    self.send(self.offset, self.type, self.volume_per[i+1],
                              self.bidprice if self.offset == 'buy' else self.askprice)
                    self.ordertime_two = now_time + datetime.timedelta(seconds=self.sids)
                    self.j = self.j + 1
                elif now_time > self.ordertime_one[i+1] and self.j == i and self.Time_per < self.sids:
                    self.sendfak(self.offset, self.type, self.volume_per[i+1],
                              self.askprice if self.offset == 'buy' else self.bidprice)
                    self.gogogo = 1
                    self.j = self.j + 1
            if self.ordertime_one != [] and now_time > self.ordertime_one[-1] and self.a == 0:
                if self.id != '':
                    self.cancelOrder(self.id)
                    time.sleep(0.2)
                    if self.vv != 0:
                        self.sendfak(self.offset, self.type, self.vv,
                                     self.askprice + 10 if self.offset == 'buy' else self.bidprice - 10)  #直接对手价超价10报单，不成交这里会导致数量缺失
                ctaEngine.removeTimer(self.sid, 22)
                self.output('已到达指定时间，算法结束')
                self.output(self.ordertime_one[-1])
                self.a = 1
        elif self.id != '' and self.offset == 'buy' and self.orderprice < self.bidprice and now_time >= self.ordertime_two:
            self.cancelOrder(self.id) #撤单要判断撤单是否成功，否者这里会出现重复发单
            time.sleep(0.1)
            if self.vv != 0:
                self.send(self.offset, self.type, self.vv,
                          self.bidprice if self.offset == 'buy' else self.askprice)
                self.ordertime_two = now_time + datetime.timedelta(seconds=self.sids)
        elif self.id != 0 and self.offset == 'sell' and self.orderprice > self.askprice and now_time >= self.ordertime_two:
            self.cancelOrder(self.id) #撤单要判断撤单是否成功，否者这里会出现重复发单
            time.sleep(0.1)
            if self.vv != 0:
                self.send(self.offset, self.type, self.vv,
                          self.bidprice if self.offset == 'buy' else self.askprice)
                self.ordertime_two = now_time + datetime.timedelta(seconds=self.sids)


    def send(self, offset, type, m, price):
        if offset == 'buy' and type == 'open':
            return self.sendOrder(CTAORDER_BUY, price, m, self.vtSymbol, self.exchange,)
        elif offset == 'sell' and type == 'open':
            return self.sendOrder(CTAORDER_SHORT, price, m, self.vtSymbol, self.exchange, )
        elif offset == 'buy' and type == 'close':
            return self.sendOrder(CTAORDER_COVER, price, m, self.vtSymbol, self.exchange,)
        elif offset == 'sell' and type == 'close':
            return self.sendOrder(CTAORDER_SELL, price, m, self.vtSymbol, self.exchange, )

    def sendfak(self, offset, type, m, price):
        if offset == 'buy' and type == 'open':
            return self.sendOrderFAK(CTAORDER_BUY, price, m, self.vtSymbol, self.exchange,)
        elif offset == 'sell' and type == 'open':
            return  self.sendOrderFAK(CTAORDER_SHORT, price, m, self.vtSymbol, self.exchange, )
        elif offset == 'buy' and type == 'close':
            return  self.sendOrderFAK(CTAORDER_COVER, price, m, self.vtSymbol, self.exchange,)
        elif offset == 'sell' and type == 'close':
            return  self.sendOrderFAK(CTAORDER_SELL, price, m, self.vtSymbol, self.exchange, )

    def onStop(self):
        ctaEngine.removeTimer(self.sid, 22)
        super().onStop()
