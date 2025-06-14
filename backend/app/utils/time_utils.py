#!/usr/bin/env python3
"""
时间处理工具类
包含时区处理、时间格式化等功能
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))


class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def now_china() -> datetime:
        """获取中国当前时间 (UTC+8)"""
        return datetime.now(CHINA_TZ)
    
    @staticmethod
    def now_china_naive() -> datetime:
        """获取中国当前时间的naive datetime对象"""
        return TimeUtils.now_china().replace(tzinfo=None)
    
    @staticmethod
    def utc_to_china(utc_dt: datetime) -> datetime:
        """将UTC时间转换为中国时间"""
        if utc_dt.tzinfo is None:
            # 假设输入是UTC时间
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        return utc_dt.astimezone(CHINA_TZ).replace(tzinfo=None)
    
    @staticmethod
    def china_to_utc(china_dt: datetime) -> datetime:
        """将中国时间转换为UTC时间"""
        if china_dt.tzinfo is None:
            # 假设输入是中国时间
            china_dt = china_dt.replace(tzinfo=CHINA_TZ)
        
        return china_dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    @staticmethod
    def format_china_time(dt: Optional[datetime] = None) -> str:
        """格式化中国时间为字符串"""
        if dt is None:
            dt = TimeUtils.now_china_naive()
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_china_timestamp_sql() -> str:
        """获取用于SQL的中国时间戳字符串"""
        return TimeUtils.format_china_time()


# 便利函数，保持向后兼容性
def now_china() -> datetime:
    """获取中国当前时间 (UTC+8) - 便利函数"""
    return TimeUtils.now_china()


def now_china_naive() -> datetime:
    """获取中国当前时间的naive datetime对象 - 便利函数"""
    return TimeUtils.now_china_naive()


def utc_to_china(utc_dt: datetime) -> datetime:
    """将UTC时间转换为中国时间 - 便利函数"""
    return TimeUtils.utc_to_china(utc_dt)


def china_to_utc(china_dt: datetime) -> datetime:
    """将中国时间转换为UTC时间 - 便利函数"""
    return TimeUtils.china_to_utc(china_dt)


def format_china_time(dt: Optional[datetime] = None) -> str:
    """格式化中国时间为字符串 - 便利函数"""
    return TimeUtils.format_china_time(dt)


def get_china_timestamp_sql() -> str:
    """获取用于SQL的中国时间戳字符串 - 便利函数"""
    return TimeUtils.get_china_timestamp_sql() 