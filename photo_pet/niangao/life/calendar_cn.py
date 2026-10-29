"""Gregorian/Chinese lunar dates. Civil time is China standard time, UTC+08:00."""
from datetime import datetime, date, timezone, timedelta
from functools import lru_cache
from lunar_python import Solar,Lunar
from dataclasses import dataclass
CHINA=timezone(timedelta(hours=8), "Asia/Shanghai")
FIRST=date(2020,1,1)
LAST=date(2069,12,31)
MONTHS=("正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊")
DAYS=("初一 初二 初三 初四 初五 初六 初七 初八 初九 初十 十一 十二 十三 十四 十五 十六 十七 十八 十九 二十 廿一 廿二 廿三 廿四 廿五 廿六 廿七 廿八 廿九 三十").split()
def china_now(timestamp=None):
    return datetime.now(CHINA) if timestamp is None else datetime.fromtimestamp(timestamp,CHINA)
@dataclass(frozen=True)
class LunarDay:
    year:int
    month:int
    day:int
    isLeapMonth:bool
    def toSolarDate(self):
        solar=Lunar.fromYmd(self.year,-self.month if self.isLeapMonth else self.month,self.day).getSolar()
        return date(solar.getYear(),solar.getMonth(),solar.getDay())
@lru_cache(maxsize=19000)
def lunar(day):
    if not FIRST<=day<=LAST:raise ValueError("日历支持 2020–2069 年")
    value=Solar.fromYmd(day.year,day.month,day.day).getLunar()
    return LunarDay(value.getYear(),abs(value.getMonth()),value.getDay(),value.getMonth()<0)
def lunar_label(day,full=False):
    value=lunar(day);month=("闰" if value.isLeapMonth else "")+MONTHS[value.month-1]+"月"
    festival={(1,1):"春节",(1,15):"元宵",(5,5):"端午",(7,7):"七夕",(8,15):"中秋",(9,9):"重阳",(12,8):"腊八"}.get((value.month,value.day)) if not value.isLeapMonth else None
    return (f"农历 {value.year}年 {month}{DAYS[value.day-1]}" if full else festival or (month if value.day==1 else DAYS[value.day-1]))
