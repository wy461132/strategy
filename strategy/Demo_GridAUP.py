from ctaBase import *
from ctaTemplate import *


class Demo_GridAUP(CtaTemplate):
    """仅供测试_定时对手价交易"""
    vtSymbol = ''
    exchange = ''
    className = 'Demo_GridAUP'
    author = 'ljt'
    name = EMPTY_UNICODE  # 策略实例名称

    # 参数映射表
    paramMap = {
        'P': '下单价格',
        'V': '下单手数',
        'off': '方向',
        'spid': '定时毫秒数',
        'bid':'是否维持当前仓位',
        'exchange': '交易所',
        'vtSymbol': '合约'
    }
    # 参数列表，保存了参数的名称
    paramList = list(paramMap.keys())
    
    # 变量映射表
    varMap = {
        'trading': '交易中',
        'pos': '仓位'
    }
    # 变量列表，保存了变量的名称
    varList = list(varMap.keys())

    off = ['buy', 'sell']

    def __init__(self, ctaEngine=None, setting={}):
        """Constructor"""
        super(Demo_GridAUP, self).__init__(ctaEngine, setting)

        self.P = 0  # 买入价
        self.V = 0  # 下单手数
        self.off = 'buy'
        self.spid = 300000
        self.bid = True
        self.buys = 5
        self.sells = 5
        self.sorder = {}
        self.torder = {}
        self.ask = ''
        self.bid = ''
        self.p = ''

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super().onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return
        self.ask = tick.askPrice1
        self.bid = tick.bidPrice1


    def onTrade(self, trade):
        super().onTrade(trade, log=True)

    def onOrder(self, order, log=False):
        if order.status == '已撤销' or order.status == '部成部撤':
            if order.offset == '开仓' and order.direction == '多':
                self.orderID = self.sendOrderFAK(CTAORDER_BUY, self.ask, order.totalVolume - order.tradedVolume,
                                                 self.vtSymbol,
                                                 self.exchange, )
            elif order.offset == '开仓' and order.direction == '空':
                self.orderID = self.sendOrderFAK(CTAORDER_SHORT, self.bid, order.totalVolume - order.tradedVolume,
                                                 self.vtSymbol,
                                                 self.exchange, )
            elif order.offset == '平仓' and order.direction == '多':
                self.orderID = self.sendOrderFAK(CTAORDER_COVER, self.ask, order.totalVolume - order.tradedVolume,
                                                 self.vtSymbol,
                                                 self.exchange, )
            elif order.offset == '平仓' and order.direction == '空':
                self.orderID = self.sendOrderFAK(CTAORDER_SELL, self.ask, order.totalVolume - order.tradedVolume,
                                                 self.vtSymbol,
                                                 self.exchange, )

        self.output(self.sorder)

    def onStart(self):
        super().onStart()
        self.manage_position()
        self.p0 = self.pos.get(self.vtSymbol)
        self.regTimer(111, int(self.spid))
        self.output('定时器已开启')
        self.output('报单已启动')
        self.p = self.pos.get(self.vtSymbol)
        self.output('净持仓:{}'.format(self.p))

    def onStop(self):
        super().onStop()
        ctaEngine.removeTimer(self.sid, 111)

    def onTimer(self, tid):
        self.manage_position()
        self.p1 = self.pos.get(self.vtSymbol)
        self.output('净持仓:{}'.format(self.p))
        if self.bid:
            if self.p1 > self.p0:
                self.orderID = self.sendOrderFAK(CTAORDER_SELL, self.ask, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.p1 < self.p0:
                self.orderID = self.sendOrderFAK(CTAORDER_COVER, self.bid, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.off == 'buy' and self.p1 == self.p0:
                self.orderID = self.sendOrderFAK(CTAORDER_BUY, self.ask, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.off == 'sell' and self.p1 == self.p0:
                self.orderID = self.sendOrderFAK(CTAORDER_SHORT, self.bid, self.V, self.vtSymbol,
                                                 self.exchange, )
        else:
            if self.p1 > 0:
                self.orderID = self.sendOrderFAK(CTAORDER_SELL, self.ask, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.p1 < 0:
                self.orderID = self.sendOrderFAK(CTAORDER_COVER, self.bid, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.off == 'buy' and self.p1 ==0:
                self.orderID = self.sendOrderFAK(CTAORDER_BUY, self.ask, self.V, self.vtSymbol,
                                                 self.exchange, )
            elif self.off == 'sell' and self.p1 ==0:
                self.orderID = self.sendOrderFAK(CTAORDER_SHORT, self.bid, self.V, self.vtSymbol,
                                                 self.exchange, )
