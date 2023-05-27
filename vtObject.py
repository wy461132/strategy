# encoding: UTF-8

"""
last update: 2023年4月25日 11:14:20
"""

import datetime
import os
import sys
import traceback
from dataclasses import dataclass
from importlib import machinery

qt_origin_path = os.path.join(sys.base_prefix, "Lib", "site-packages", "PyQt5", "Qt", "plugins")
if os.path.exists(qt_origin_path):
    #: 正确设置 QT 路径
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_origin_path

sys.path.append('.\\pyStrategy\\')
sys.path.append(os.path.split(os.path.realpath(__file__))[0])

import ctaEngine  # type: ignore

from vtConstant import *

product_cls = {
    '1': '期货',
    '2': '期权',
    '3': '组合',
    '4': '即期',
    '5': '期转现',
    '6': '未知类型',
    '7': '证券',
    '8': '股票期权',
    '9': '金交所现货',
    'a': '金交所递延',
    'b': '金交所远期',
    'h': '现货期权'
}

option_type = {
    '0': '非期权',
    '1': '看涨',
    '2': '看跌'
}


class VtBaseData(object):
    """回调函数推送数据的基础类，其他数据类继承于此"""
    def __init__(self):
        self.gatewayName = ''  # Gateway名称
        self.rawData = None  # 原始数据


class VtTickData(VtBaseData):
    """
    Tick行情数据类,来源为交易所推送的行情切片
    """
    def __init__(self):
        super().__init__()

        # 代码相关
        self.symbol = ''  # 合约代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 合约代码.交易所代码

        # 成交数据
        self.lastPrice = 0.0  # 最新成交价
        self.lastVolume = 0  # 最新成交量
        self.volume = 0  # 今天总成交量
        self.openInterest = 0  # 持仓量
        self.time = ''  # 时间 11:20:56.5
        self.date = ''  # 日期 20151009
        self.datetime: datetime.datetime = None  # 合约时间

        # 常规行情
        self.openPrice = 0.0  # 今日开盘价
        self.highPrice = 0.0  # 今日最高价
        self.lowPrice = 0.0  # 今日最低价
        self.preClosePrice = 0.0  # 昨收盘价
        self.PreSettlementPrice = 0.0  # 昨结算价

        self.upperLimit = 0.0  # 涨停价
        self.lowerLimit = 0.0  # 跌停价

        self.turnover = 0.0  # 成交额

        # 五档行情
        self.bidPrice1 = 0.0
        self.bidPrice2 = 0.0
        self.bidPrice3 = 0.0
        self.bidPrice4 = 0.0
        self.bidPrice5 = 0.0

        self.askPrice1 = 0.0
        self.askPrice2 = 0.0
        self.askPrice3 = 0.0
        self.askPrice4 = 0.0
        self.askPrice5 = 0.0

        self.bidVolume1 = 0
        self.bidVolume2 = 0
        self.bidVolume3 = 0
        self.bidVolume4 = 0
        self.bidVolume5 = 0

        self.askVolume1 = 0
        self.askVolume2 = 0
        self.askVolume3 = 0
        self.askVolume4 = 0
        self.askVolume5 = 0


@dataclass
class TickData(VtTickData):
    """带最新成交量的最新 Tick 数据"""
    _cache_volume = 0 # 缓存总成交量

    @property
    def last_volume(self) -> int:
        """最新成交量"""
        last_volume: int = self.volume - self._cache_volume

        if not self._cache_volume:
            last_volume = 0

        self._cache_volume = self.volume
        return last_volume

    def update(self, tick: VtTickData) -> None:
        """更新 Tick 数据"""
        self.__dict__.update(tick.__dict__)


class VtTradeData(VtBaseData):
    """
    成交数据类,来源为交易所推送的成交回报
    """
    def __init__(self):
        super().__init__()

        # 代码编号相关
        self.symbol = ''  # 合约代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 合约代码.交易所代码

        self.tradeID = ''  # 成交编号
        self.vtTradeID = ''  # 成交编号

        self.orderID = ''  # 订单编号
        self.vtOrderID = ''  # 订单编号
        self.memo = '' # 订单备注

        # 成交相关
        self.direction = ''  # 成交方向
        self.offset = ''  # 成交开平仓
        self.price = 0.0  # 成交价格
        self.volume = 0  # 成交数量
        self.tradeTime = ''  # 成交时间

        self.commission = 0.0  # 手续费


class VtOrderData(VtBaseData):
    """
    订单数据类,来源为交易所推送的委托回报
    """
    def __init__(self):
        super().__init__()
        # 代码编号相关
        self.symbol = ''  # 合约代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 交易所代码

        self.orderID = ''  # 订单编号
        self.vtOrderID = ''  # 订单编号
        self.memo = '' # 订单备注

        # 报单相关
        self.direction = ''  # 报单方向
        self.offset = ''  # 报单开平仓
        self.price = 0.0  # 报单价格
        self.priceType = ''  # 报单价格
        self.totalVolume = 0  # 报单总数量
        self.tradedVolume = 0  # 报单成交数量
        self.status = ''  # 报单状态

        self.orderTime = ''  # 发单时间
        self.cancelTime = ''  # 撤单时间

        # CTP/LTS相关
        self.frontID = 0  # 前置机编号
        self.sessionID = 0  # 连接编号


class VtBarData(VtBaseData):
    """K线数据"""
    def __init__(self):
        super().__init__()
        self.vtSymbol = ''  # vt系统代码
        self.symbol = ''  # 代码
        self.exchange = ''  # 交易所

        self.open = 0.0  # OHLC
        self.high = 0.0
        self.low = 0.0
        self.close = 0.0

        self.date = ''  # bar开始的时间，日期
        self.time = ''  # 时间
        self.datetime: datetime.datetime = None  # python的datetime时间对象

        self.volume = 0  # 成交量
        self.openInterest = 0  # 持仓量


class VtPositionData(VtBaseData):
    """持仓数据类"""
    def __init__(self):
        super().__init__()
        # 代码编号相关
        self.symbol = ''  # 合约代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 合约在vt系统中的唯一代码，合约代码.交易所代码

        # 持仓相关
        self.direction = ''  # 持仓方向
        self.position = 0  # 持仓量
        self.frozen = 0  # 冻结数量

        self.open_avg_price = 0  # 开仓均价
        self.position_avt_price = 0.0  # 持仓均价
        self.postion_cost = 0  # 持仓成本

        self.vtPositionName = ''  # 持仓在vt系统中的唯一代码，通常是vtSymbol.方向
        self.investorID = ''  # 投资者
        self.investor = ''  # 投资者
        self.positionProfit = 0.0  # 平仓盈亏

        # 20151020添加
        self.ydPosition = 0  # 昨持仓

        self.close_available = 0 # 可用数量/可平仓量(不包含平仓冻结)


class VtAccountData(VtBaseData):
    """账户数据类"""
    def __init__(self):
        super().__init__()
        # 账号代码相关
        self.datetime: datetime.datetime = None
        self.accountID = ''  # 账户代码
        self.vtAccountID = ''  # 账户在vt中的唯一代码，通常是 Gateway名.账户代码

        # 数值相关
        self.preBalance = 0.0  # 昨日账户结算净值
        self.balance = 0.0  # 账户净值
        self.available = 0.0  # 可用资金
        self.commission = 0.0  # 今日手续费
        self.margin = 0.0  # 保证金占用
        self.closeProfit = 0.0  # 平仓盈亏
        self.positionProfit = 0.0  # 持仓盈亏


class VtContractData(VtBaseData):
    """合约详细信息类"""
    def __init__(self):
        super().__init__()
        self.symbol = ''  # 代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 合约代码.交易所代码
        self.name = ''  # 合约中文名

        self.productClass = ''  # 合约类型
        self.size = 0  # 合约大小（合约乘数）
        self.priceTick = 0.0  # 合约最小价格TICK
        self.min_limit_order_volume = 0 # 最小下单量
        self.expire_date = '' # 合约到期日

        # 期权相关
        self.strikePrice = 0.0  # 期权行权价
        self.underlyingSymbol = ''  # 标的物合约代码
        self.optionType = ''  # 期权类型


class VtContractStatusData(VtBaseData):
    """合约状态类"""
    def __init__(self):
        """Constructor"""
        super().__init__()
        self.symbol = ''  # 代码
        self.exchange = ''  # 交易所代码
        self.vtSymbol = ''  # 合约代码.交易所代码
        self.status = ''  # 报单状态


def importStrategy(path):
    """导入 Python 策略"""
    errCode = ''
    try:
        file_name = path.split("\\")[-1]
        model_name = file_name.split(".")[0]
        machinery.SourceFileLoader('ctaStrategies', path).load_module()
        if not hasattr(sys.modules['ctaStrategies'], model_name):
            ctaEngine.writeLog(f'该策略文件名: {file_name} 和类名不一致, 请修改')
            return 'error', None
        return errCode, getattr(sys.modules['ctaStrategies'], model_name)
    except:
        errCode = traceback.format_exc()
        errCode = errCode.replace('\n', '\r\n')
        return errCode, None


def safeDatetime(timeStr):
    """策略的时间"""
    # 如果行情没有返回date，手动拼接
    if timeStr.startswith(" "):
        timeStr = timeStr.strip()
        if timeStr == '0' or timeStr == '.0' or not timeStr:
            return datetime.datetime.now()
        else:
            timeStr = f'{datetime.datetime.now().date()} {timeStr}'
            return datetime.datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S.%f")
    try:
        return datetime.datetime.strptime(timeStr, "%Y%m%d %H:%M:%S.%f")
    except:
        try:
            return datetime.datetime.strptime(timeStr, "%Y%m%d %H%M%S.%f")
        except:
            return datetime.datetime.now()


def safeCall(pyFunc, pyArgs=()):
    """创建策略实例
    pyFunc: onStop, onInit等各种方法的对象
    pyRes: 策略参数的对象
    pyArgs: 一排() + tick对象
    """
    try:
        pyRes = pyFunc(*pyArgs)
        return pyRes
    except:
        errCode = '\r\n'.join([str(pyFunc), traceback.format_exc()])
        errCode = errCode.replace('\n', '\r\n')
        ctaEngine.writeLog(errCode)
        return 'error'


# ----------------------------------------------------------------------
def onExit():
    """引擎退出"""
    CtaTemplate.t = None
