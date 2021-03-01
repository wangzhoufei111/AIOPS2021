""" Demo1
    测试1: Generate Nsigma
    Input: ts, 足够长的时间序列
    Output: n_upper, n_lower, stds列表
"""

import numpy as np
import pandas as pd
from detection.utils.timeconvert import strtime_to_timestamp, timestamp_to_datetime
from detection.statistic.generate_standard_nsigma import GeneratorStandardNsigma

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


def run(i = 0, instance_type = 'mrt'):
    """ 测试ts生成统计量
    """

    start_time = '2021-01-28 00:00:00'
    end_time = '2021-01-30 23:59:59'

    kpi_paths = ['kpi_0128.csv', 'kpi_0129.csv', 'kpi_0130.csv']
    kpi_data = pd.DataFrame()
    for path in kpi_paths:
        kpi_data = kpi_data.append(pd.read_csv(path, encoding='gb18030'))
    kpi_names = list(set(kpi_data['tc']))

    one = kpi_data[kpi_data['tc'] == kpi_names[i]]
    dt_list, timestamp_list  = generate_time_list(start_time, end_time, 60)
    data_merge = padding_ts(dt_list, timestamp_list, one)
    data_merge = data_merge.fillna(-1)

    exe = GeneratorStandardNsigma()
    ts = [i if i != -1  else None for i in list(data_merge['mrt'])]
    n_upper, n_lower, stds = exe.run(ts)
    print('n_upper:{0} \nn_lower:{1}'.format(str(n_upper), str(n_lower)))
    print('stds标准差序列:')
    print(stds)