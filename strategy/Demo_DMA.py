# encoding: UTF-8

"""
双均线策略
last update: 2022年7月22日 14:10:54
"""

from traceback import format_exc

from ctaBase import *
from ctaTemplate import *


class Demo_DMA(CtaTemplate):
    """仅供测试_可调节K线周期的双均线交易策略"""
    vtSymbol = ''
    exchange = ''
    className = 'Demo_DMA'
    author = 'LJT'
    name = ''  # 策略实例名称

    # 策略参数
    N = 5 #: 快均线周期
    P = 20 #: 慢均线周期
    initDays = 10 #: 初始化数据所用的天数

    # 策略变量
    ma0 = 0 #: 当前K线慢均线数值
    ma1 = 0 #: 当前K线快均线数值
    ma00 = 0 #: 上一个K线慢均线数值
    ma10 = 0 #: 上一个K线快均线数值

    # 参数映射表
    paramMap = {
        'exchange': '交易所',
        'vtSymbol': '合约',
        'N': '快均线周期',
        'P': '慢均线周期',
        'volume': '下单手数',
        'nMin': 'K线分钟',
        'D': '超价Tick'
    }

    # 参数列表，保存了参数的名称
    paramList = list(paramMap.keys())
    
    # 变量映射表
    varMap = {
        'trading': '交易中',
        'ma0': '慢均线',
        'ma1': '快均线',
        'pos': '持仓'
    }

    # 变量列表，保存了变量的名称
    varList = list(varMap.keys())

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine=None, setting={}):
        """Constructor"""
        super().__init__(ctaEngine, setting)

        self.widgetClass = KLWidget
        self.widget = None
        self.nMin = 5
        self.cost = 0  # 持仓成本

        self.volume = 1  # 下单手数
        self.ma0 = 0  # 当前K线慢均线数值
        self.ma1 = 0  # 当前K线快均线数值
        self.ma00 = 0  # 上一个K线慢均线数值

        self.ma10 = 0  # 上一个K线快均线数值
        self.D=0
        self.trading = False

        # 启动界面
        self.signal = 0  # 买卖标志
        self.mainSigs = ['ma0', 'ma1', 'cost']  # 主图显示
        self.subSigs = []  # 副图显示
        self.getGui()

        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        super().onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return
        self.bm.updateTick(tick)

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bar = bar
        if self.tradeDate != bar.date:
            self.tradeDate = bar.date

        # 记录数据
        if not self.bm.updateBar(bar):
            return

    def onBarX(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bar = bar

        # 记录数据
        if not self.am.updateBar(bar):
            return

        # 计算指标
        self.getCtaIndictor(bar)

        # 计算信号
        self.getCtaSignal(bar)

        # 简易信号执行
        self.execSignal(self.volume)

        # 前收盘
        self.refclose = bar.close

        # 发出状态更新事件
        if (not self.widget is None) and (not self.bar is None):
            data = {'bar': self.bar, 'sig': self.signal, 'ma0': self.ma0, 'ma1': self.ma1, 'cost': self.cost}
            self.widget.addBar(data)
        if self.trading:
            self.putEvent()

    def getCtaIndictor(self, bar):
        """计算指标数据"""
        # 计算指标数值
        ma = self.am.sma(self.P, True)
        ma1 = self.am.sma(self.N, True)
        self.ma0, self.ma00 = ma[-1], ma[-2]
        self.ma1, self.ma10 = ma1[-1], ma1[-2]

    def getCtaSignal(self, bar):
        """计算交易信号"""
        close = bar.close
        hour = bar.datetime.hour
        minute = bar.datetime.minute
        # 定义尾盘，尾盘不交易并且空仓
        self.endOfDay = hour == 14 and minute >= 40
        # 判断是否要进行交易
        self.buySig = self.ma1 > self.ma0 and self.ma10 < self.ma00
        self.shortSig = self.ma1 < self.ma0 and self.ma10 > self.ma00
        # 交易价格
        self.longPrice = bar.close
        self.shortPrice = bar.close

    def execSignal(self, volume):
        """简易交易信号执行"""
        pos = self.pos[self.vtSymbol]
        # 挂单未成交
        if self.orderID is not None:
            self.cancelOrder(self.orderID)

        self.signal = 0

        if pos == 0 and not self.endOfDay: #: 当前无仓位
            # 买开，卖开    
            if self.shortSig:
                self.signal = -self.shortPrice
                self.orderID = self.short(self.shortPrice - self.D, volume)
                self.output('卖出开仓信号价格：{}'.format(self.shortPrice - self.D))
            elif self.buySig:
                self.signal = self.longPrice
                self.orderID = self.buy(self.longPrice + self.D, volume)
                self.output('买入开仓信号价格：{}'.format(self.longPrice + self.D))
        elif pos > 0 and self.shortSig: #: 持有多头仓位
            self.signal = -self.shortPrice
            self.orderID = self.sell(self.shortPrice - self.D, pos)
            self.output('卖出平仓信号价格：{}'.format(self.shortPrice - self.D))
        elif pos < 0 and self.buySig: #: 持有空头仓位
            self.signal = self.longPrice
            self.orderID = self.cover(self.longPrice + self.D, -pos)
            self.output('买入平仓信号价格：{}'.format(self.longPrice + self.D))

    def onInit(self):
        """本策略刚加载的时候不需要显示 QT 界面"""
        super().onInit()
        self.closeGui()

    def onTrade(self, trade, log=True):
        super().onTrade(trade, log)

    def onStart(self):
        self.getGui()
        self.bm = BarManager(self.onBar, self.nMin, self.onBarX)
        self.am = ArrayManager(size=40)
        try:
            #: 当从加载实例中启动策略时, K 线图为空, 则需要把 qt_gui 设为 True
            self.loadBar(10, qt_gui=True)
        except (TypeError, ValueError) as e:
            self.output(format_exc())
            self.onStop()
            return StatusCode.stop
        super().onStart()

    def onStop(self):
        super().onStop()
