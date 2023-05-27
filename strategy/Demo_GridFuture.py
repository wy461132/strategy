# encoding: UTF-8

"""
开-平 全量网格

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
"""

from ctaBase import *
from ctaTemplate import *


class Demo_GridFuture(CtaTemplate):
    """仅供测试_开-平 全量网格"""
    vtSymbol = ''
    exchange = ''
    className = 'Demo_GridFuture'
    author = 'ljt'
    name = EMPTY_UNICODE                # 策略实例名称

    # 参数映射表
    paramMap = {
        'P': '下单价格',
        'V': '下单手数',
        'off': '方向',
        'type': '开平',
        'spid': '逐笔间隔',
        'bid': '委托笔数',
        'buys': '多单参数',
        'sells': '空单参数',
        'exchange': '交易所',
        'vtSymbol': '合约'
    }
    # 参数列表，保存了参数的名称
    paramList = list(paramMap.keys())

    # 变量映射表
    varMap   = {
        'trading' : '交易中',
        'pos': '仓位'
    }
    # 变量列表，保存了变量的名称
    varList = list(varMap.keys())


    def __init__(self,ctaEngine=None,setting={}):
        """Constructor"""
        super().__init__(ctaEngine,setting)
        self.P = 0 # 买入触发价
        self.V = 0 # 下单手数
        self.off = 'buy' # buy or sell
        self.type = 'open' # open or close
        self.spid = 1
        self.bid = 0
        self.buys = 5
        self.sells = 5
        self.bv = 0
        self.sv = 0
        self.bvv = 0
        self.svv = 0


    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super().onTick(tick)


    def onTrade(self, trade):
        super().onTrade(trade,log=True)
        if trade.direction == '多' and trade.offset == '开仓':
            self.orderID = self.sendOrder(CTAORDER_SELL, trade.price + self.buys, trade.volume, self.vtSymbol,
                                          self.exchange, )
        elif trade.direction == '空' and trade.offset == '开仓':
            self.orderID = self.sendOrder(CTAORDER_COVER, trade.price - self.sells, trade.volume, self.vtSymbol,
                                               self.exchange, )
        elif trade.direction == '空' and trade.offset == '平仓':
            self.orderID = self.sendOrder(CTAORDER_BUY, trade.price - self.sells, trade.volume, self.vtSymbol,
                                          self.exchange, )
        elif trade.direction == '多' and trade.offset == '平仓':
            self.orderID = self.sendOrder(CTAORDER_SHORT, trade.price + self.buys, trade.volume, self.vtSymbol,
                                          self.exchange, )

    def onStart(self):
        super().onStart()
        self.manage_position()
        self.output('报单已启动')
        if self.type == 'open':
            if self.off == 'buy' and self.bid == 0:
                self.orderID = self.sendOrder(CTAORDER_BUY, self.P, self.V, self.vtSymbol, self.exchange, )
            elif self.off == 'sell' and self.bid == 0:
                self.orderID = self.sendOrder(CTAORDER_SHORT, self.P, self.V, self.vtSymbol, self.exchange, )
            elif self.off == 'buy' and self.bid != 0:
                for i in range(0,self.bid):
                    self.orderID = self.sendOrder(CTAORDER_BUY, self.P - i * self.spid, self.V, self.vtSymbol, self.exchange, )
            elif self.off == 'sell' and self.bid != 0:
                for i in range(0,self.bid):
                    self.orderID = self.sendOrder(CTAORDER_SHORT, self.P + i * self.spid, self.V, self.vtSymbol, self.exchange, )
        elif self.type == 'close':
            if self.off == 'buy' and self.bid == 0:
                self.orderID = self.sendOrder(CTAORDER_COVER, self.P, self.V, self.vtSymbol, self.exchange, )
            elif self.off == 'sell' and self.bid == 0:
                self.orderID = self.sendOrder(CTAORDER_SELL, self.P, self.V, self.vtSymbol, self.exchange, )
            elif self.off == 'buy' and self.bid != 0:
                for i in range(0, self.bid):
                    self.orderID = self.sendOrder(CTAORDER_COVER, self.P - i * self.spid, self.V, self.vtSymbol,
                                                  self.exchange, )
            elif self.off == 'sell' and self.bid != 0:
                for i in range(0, self.bid):
                    self.orderID = self.sendOrder(CTAORDER_SELL, self.P + i * self.spid, self.V, self.vtSymbol,
                                                  self.exchange, )

    def onStop(self):
        super().onStop()
