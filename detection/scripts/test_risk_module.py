""" Test 风险事件模型
"""

import numpy as np
import pandas as pd
from detection.detecter import Detecter
from detection.utils.timeconvert import strtime_to_timestamp, timestamp_to_datetime, datetime_to_strtime


def generate_time_list(start_time, end_time, sample_period = 60):
    """ Generate time list
    """
    
    dt_list = []
    timestamp_list = []
    
    start_timestamp = strtime_to_timestamp(start_time)
    end_timestamp = strtime_to_timestamp(end_time)
    
    for t in np.arange(start_timestamp, end_timestamp, sample_period):
        dt_list.append(timestamp_to_datetime(t))
        timestamp_list.append(t)
    
    return dt_list, timestamp_list

def padding_ts(dt_list, timestamp_list, data):
    """ Padding ts
    """
    
    time_df = pd.DataFrame()
    time_df['datetime'] = dt_list
    time_df['timestamp'] = timestamp_list
    
    data_merge = pd.merge(time_df, data, how = 'left', on = ['timestamp'])
    
    return data_merge


def run(i = 1, instance_type = 'mrt'):
    """ 测试ts生成统计量
        from detection.scripts.test_risk_module import run
    """

    start_time = '2021-01-28 00:00:00'
    end_time = '2021-01-30 23:59:59'

    kpi_paths = ['kpi_0128.csv', 'kpi_0129.csv', 'kpi_0130.csv']
    kpi_data = pd.DataFrame()
    for path in kpi_paths:
        d = pd.read_csv(path, encoding='gb18030')
        if 'kpi_0128' in path:
            d = d.rename(columns={'count':'cnt'})
        kpi_data = kpi_data.append(d)
    kpi_data = kpi_data.reset_index(drop=True)
    kpi_names = list(set(kpi_data['tc']))

    one = kpi_data[kpi_data['tc'] == kpi_names[i]]
    dt_list, timestamp_list  = generate_time_list(start_time, end_time, 60)
    data_merge = padding_ts(dt_list, timestamp_list, one)
    data_merge = data_merge.dropna().reset_index(drop=True)

    ts = []
    for j in range(len(data_merge)):
        ts.append([datetime_to_strtime(data_merge.loc[j, 'datetime']), data_merge.loc[j,'mrt']])

    exe = Detecter(ts, kpi_names[i], 'mrt').run()
