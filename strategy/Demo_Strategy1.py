# encoding: UTF-8
"""
监控当价格于某个时间点突破某价格时买入或价格下跌突破某价格时卖出
可自由选择是否开启时间控制
"""

import datetime

from ctaTemplate import *


class Demo_Strategy1(CtaTemplate):
    """仅供测试_基于时间的单合约价格触发交易策略"""
    className = 'Demo_Strategy1'
    author = 'rock'

    # 参数映射表
    paramMap = {
        'vtSymbol': '合约',
        'exchange': '交易所',
        'volume': '下单手数',
        'buy_price': '买入价格',
        'sell_price': '卖出价格',
        'trigger_time': '触发时间',
        'is_on_time': '是否开启时间控制'
    }
    # 参数列表
    paramList = list(paramMap.keys())

    # 变量映射表
    varMap = {
        'trading': '交易中',
        'time': '当前时间',
        'pos': '当前持仓'
    }
    # 变量列表
    varList = list(varMap.keys())

    def __init__(self, ctaEngine=None, setting={}):
        """Constructor"""
        super().__init__(ctaEngine, setting)
        self.volume = 1
        self.buy_price = 0.0
        self.sell_price = 0.0
        self.trigger_time = '14:00:00'
        # 修改此开关时首字母一定要大写
        self.is_on_time = False
        self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 用来标识是否已买开和卖开，避免重复发单
        self.has_buy = False
        self.has_sell = False

    def onTick(self, tick):
        super().onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return

        # 更新时间
        self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 计算交易信号
        self.get_signal(tick)

        # 执行交易信号
        self.exec_signal(tick)

        # 推送状态
        self.putEvent()


    def get_signal(self, tick):
        if self.is_on_time is True:
            # 考虑到有丢tick的情况，暂定在指定时间内的前后2s之间tick价格达到要求就发单
            if (datetime.datetime.strptime(self.trigger_time, '%H:%M:%S') - datetime.timedelta(
                    seconds=2)).time() < datetime.datetime.strptime(tick.time.split('.')[0], '%H:%M:%S').time() < (
                    datetime.datetime.strptime(self.trigger_time, '%H:%M:%S') - datetime.timedelta(seconds=-2)).time():
                if tick.lastPrice >= self.buy_price:
                    self.buySig = True
                if tick.lastPrice <= self.sell_price:
                    self.sellSig = True
        # 不开启时间控制的情况
        else:
            if tick.lastPrice >= self.buy_price:
                self.buySig = True
            if tick.lastPrice <= self.sell_price:
                self.sellSig = True

    def exec_signal(self, tick):
        pos = self.pos[self.vtSymbol]
        if self.buySig and not self.has_buy:
            self.orderID = self.buy(tick.upperLimit, self.volume)
            self.buySig = False
            self.has_buy = True
        if self.sellSig and not self.has_sell and pos > 0:
            self.orderID = self.sell(tick.lowerLimit, self.volume)
            self.sellSig = False
            self.has_sell = True

    def onTrade(self, trade, log=True):
        super().onTrade(trade, log)

    def onOrder(self, order, log=True):
        super().onOrder(order, log)

    def onStart(self):
        super().onStart()
        self.manage_position()

        # 策略实例停止时，重置已买开标识和已卖标识为False
        # 所以暂停实例后，再次开始时会重置该标识
        self.has_buy = False
        self.has_sell = False
        # 确保重新启动策略时不会直接同时买开卖平
        self.buySig = False
        self.sellSig = False

    def onStop(self):
        super().onStop()
