from datetime import datetime, timedelta
from typing import Callable, List

from vtObject import VtBarData, VtTickData


class KLineGenerator(object):
    """秒级 K 线生成器

    Args:
        callback: 推送 K 线回调, 也可以是任何接受一根 K 线然后返回 None 的函数
        seconds: 合成秒数
    """
    def __init__(self, callback: Callable[[VtBarData], None], seconds: int = 1) -> None:
        self.callback = callback
        self.seconds = seconds

        self.cache_kline: VtBarData = None
        self.last_tick: VtTickData = None
        self.is_new: bool = True
        self.timekeeper: List[datetime] = []

    @property
    def seconds(self) -> int:
        return self._seconds

    @seconds.setter
    def seconds(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("秒数必须为 int 类型")
        self._seconds: int = value

    @property
    def first_time(self) -> datetime:
        """获取第一条 tick 的时间"""
        return self.timekeeper[0]

    @property
    def last_k_time(self) -> datetime:
        """获取上一条 K 线的时间"""
        return self.sort_timekeeper[self.seconds - 1]

    @property
    def sort_timekeeper(self) -> List[datetime]:
        """对时间线去重"""
        return sorted(set(self.timekeeper), key=self.timekeeper.index)

    def save_time(self, _time: datetime) -> None:
        """对时间去除毫秒数并保存至时间线"""
        self.timekeeper.append(_time.replace(microsecond=0))

    def _ts(self, _datetime: datetime) -> int:
        """获取 datetime 对象的时间戳"""
        return int(_datetime.timestamp())

    def fix_timeline(self, tick: VtTickData) -> None:
        """修复时间线中缺失的时间"""
        lost_seconds: int = self._ts(tick.datetime) - self._ts(self.last_tick.datetime)
        if (lost_ticks := (lost_seconds - 1)) > 0:
            # 如果少了 tick，则手动补全 timekeeper
            for j in range(lost_ticks, 0, -1):
                self.timekeeper.insert(-1, (tick.datetime - timedelta(seconds=j)).replace(microsecond=0))

    def set_kline_data(self, **kwargs) -> None:
        """对当前缓存的 K 线设置数据"""
        self.cache_kline.__dict__.update(kwargs)

    def new_kline_cycle(self, tick: VtTickData) -> bool:
        """判断该 tick 是否进入新的 K 线周期"""
        if not self.cache_kline:
            # 首次运行
            return False

        diff_seconds: int = self._ts(tick.datetime) - self._ts(self.first_time)

        self.fix_timeline(tick)

        if diff_seconds >= self.seconds:
            # 新 tick 时间和时间容器中第一根 tick 时间秒数对比
            # 如果大于等于设置的秒数，则表示进入新的 K线周期
            # 然后要修复时间线，在把时间线中正确的时间赋予当前缓存 K 线
            # 最后把该 K 线时间之后的时间重新赋值给时间线，成为新的时间线

            self.set_kline_data(
                date=self.last_k_time.strftime("%Y%m%d"),
                time=self.last_k_time.strftime("%X"),
                datetime=self.last_k_time
            )
            self.timekeeper = self.sort_timekeeper[self.seconds:]

            return True

    def tick_to_kline(self, tick: VtTickData) -> None:
        if self.is_new and tick.datetime.microsecond >= 500000:
            # 第一次运行，要毫秒数要小于 500ms，并且 self.seconds 能被 tick 的秒数整除
            return

        self.save_time(tick.datetime)

        if self.new_kline_cycle(tick):
            self.is_new = True
            self.callback(self.cache_kline)

        if self.is_new:
            self.is_new = False
            self.cache_kline = VtBarData()

            self.set_kline_data(
                vtSymbol=tick.symbol,
                symbol=tick.symbol,
                exchange=tick.exchange,
                open=tick.lastPrice,
                close=tick.lastPrice,
                high=tick.lastPrice,
                low=tick.lastPrice,
                date=tick.date,
                time=tick.time,
                datetime=tick.datetime,
                openInterest=tick.openInterest
            )
        else:
            self.set_kline_data(
                close=tick.lastPrice,
                high=max(self.cache_kline.high, tick.lastPrice),
                low=min(self.cache_kline.low, tick.lastPrice),
                volume=self.cache_kline.volume + (tick.volume - self.last_tick.volume)
            )

        self.last_tick = tick


def isdigit(value: str) -> bool:
    """判断字符串是否小数"""
    value: str = value.lstrip('-')
    if value.isdigit():
        return True
    if value.count(".") == 1 \
        and not value.startswith(".") \
        and not value.endswith(".") \
        and value.replace(".", "").isdigit():
        return True
    return False
