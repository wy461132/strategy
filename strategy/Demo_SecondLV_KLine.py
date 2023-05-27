"""
秒级 K 线
last update: 2023年3月10日 15:47:24
"""

from ctaTemplate import CtaTemplate, KLWidget, VtBarData, VtTickData
from utils import KLineGenerator


class Demo_SecondLV_KLine(CtaTemplate):
    """秒级 K 线图示例"""
    className = 'Demo_SecondLV_KLine'

    paramMap = {
        'exchange': '交易所',
        'vtSymbol': '合约',
        'seconds': '秒数'
    }
    paramList = list(paramMap.keys())

    varMap = {
        'trading': '交易中'
    }
    varList = list(varMap.keys())

    def __init__(self, ctaEngine=None, setting={}):
        super().__init__(ctaEngine, setting)

        self.widgetClass = KLWidget
        self.widget: KLWidget = None
        self.kline_generator: KLineGenerator = None

        self.exchange = ''
        self.vtSymbol = ''
        self.seconds = 5

        self.signal = 0
        self.mainSigs = []
        self.subSigs = []

        self.getGui()

    def onInit(self):
        super().onInit()
        self.closeGui()

    def onTick(self, tick: VtTickData) -> None:
        super().onTick(tick)
        self.kline_generator.tick_to_kline(tick)

    def onStart(self) -> None:
        self.kline_generator = KLineGenerator(
            callback=self.on_secend_kline,
            seconds=self.seconds
        )
        self.getGui()
        super().onStart()

    def on_secend_kline(self, bar: VtBarData) -> None:
        """推送 K 线回调, 由于不使用 signal, 所以该值默认为 0"""
        self.widget and self.widget.addBar({
            'bar': bar,
            'sig': self.signal
        })
