# -*- coding: utf-8 -*-


import time
from datetime import datetime


def timestamp_to_strtime(timestamp):
    """
    将10位整数秒级时间戳转化成字符串时间格式
    :param timestamp: 1521081438
    :return:'2018/3/15 10:37:18'
    """
    strtime = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return strtime


def timestamp_to_datetime(timestamp):
    """
    将10位整数秒级时间戳转化成datetime时间格式
    :param timestamp: 1521081438
    :return: {datetime}2018-03-15 10:37:18
    """
    datetime_obj = datetime.fromtimestamp(timestamp)
    return datetime_obj


def datetime_to_timestamp(datetime_obj):
    """
    将datetime 格式时间转化成10位时间戳格式
    :param datetime_obj: {datetime}2018-03-15 10:37:18
    :return:1521081438
    """
    timestamp = int(time.mktime(datetime_obj.timetuple()))
    return timestamp


def datetime_to_strtime(datetime_obj):
    """
    将datetime 格式时间转换成字符串格式时间
    :param datetime_obj: {datetime}2018-03-15 10:37:18
    :return: 2018-03-15 10:37:18'
    """
    strtime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return strtime


def strtime_to_datetime(strtime):
    """
    将字符串格式时间转换成datetime格式时间
    :param strtime: '2018-03-15 10:37:18'
    :return: {datetime}2018-03-15 10:37:18
    """
    datetime_obj = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    return datetime_obj


def strtime_to_timestamp(strtime):
    """
    将字符串格式时间转换成10位时间戳
    :param strtime:'2018-03-15 10:37:18'
    :return:1521081438
    """
    datetime_obj = strtime_to_datetime(strtime)
    timestamp = datetime_to_timestamp(datetime_obj)
    return timestamp


def strtime_to_ymdh(strtime):
    """
    将字符串时间格式转换成年月日小时
    :param strtime: 2018-03-15 10:37:18'
    :return: 2018031510
    """
    timearray = time.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    ymdh = time.strftime('%Y%m%d%H', timearray)
    return ymdh


def compute_timedelta(firsttime, secondtime):
    """
    计算两者时间差，秒级
    :param firsttime: "2018-03-19 16:04:01
    :param secondtime: "2018-03-19 16:24:01"
    :return: 1800
    """
    firsttime = strtime_to_datetime(firsttime)
    secondtime = strtime_to_datetime(secondtime)
    return (firsttime - secondtime).seconds