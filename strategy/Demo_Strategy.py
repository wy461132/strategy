# encoding: UTF-8
"""
last update: 2022年11月2日 16:54:05
"""
from ctaBase import *
from ctaTemplate import *


class Demo_Strategy(CtaTemplate):
    """仅供测试_超过价格发单 (支持多合约)"""
    vtSymbol = ''
    exchange = ''
    className = 'Demo_Strategy'

    # 参数映射表
    paramMap = {
        'order_price': '买触发价',
        'order_volume': '下单手数',
        'exchange': '交易所',
        'vtSymbol': '合约'
    }
    # 参数列表，保存了参数的名称
    paramList = list(paramMap.keys())

    # 变量映射表
    varMap   = {
        'trading': '交易中',
        'pos': '仓位'
    }
    # 变量列表，保存了变量的名称
    varList = list(varMap.keys())

    def __init__(self, ctaEngine=None, setting={}):
        """Constructor"""
        super().__init__(ctaEngine, setting)
        self.order_price = 100 # 买入触发价
        self.order_volume = 1 # 下单手数

    def onTick(self, tick: VtTickData):
        """收到行情TICK推送（必须由用户继承实现）"""
        super().onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return
        if tick.lastPrice > self.order_price:
            self.orderID = self.buy_fak(
                price=tick.lowerLimit,
                volume=self.order_volume,
                symbol=tick.symbol,
                exchange=tick.exchange
            )

    def onTrade(self, trade: VtTradeData):
        super().onTrade(trade, log=True)

    def onStart(self):
        super().onStart()
