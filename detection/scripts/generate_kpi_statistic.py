""" 生成StatisticMetirc表
"""

import json
import numpy as np
import pandas as pd
from detection.models import StatisticMetric
from detection.statistic.generate_standard_nsigma import GeneratorStandardNsigma
from detection.utils.timeconvert import strtime_to_timestamp, timestamp_to_datetime


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


def run():
    """ Running
        from detection.scripts.generate_kpi_statistic import run
    """

    kpi_paths = ['kpi_0128.csv', 'kpi_0129.csv', 'kpi_0130.csv']
    kpi_data = pd.DataFrame()
    for path in kpi_paths:
        d = pd.read_csv(path, encoding='gb18030')
        if 'kpi_0128' in path:
            d = d.rename(columns={'count':'cnt'})
        kpi_data = kpi_data.append(d)
    kpi_data = kpi_data.reset_index(drop=True)

    kpi_names = list(set(kpi_data['tc']))
    types = ['rr', 'sr', 'cnt', 'mrt']
    exe = GeneratorStandardNsigma()
    for i in range(len(kpi_names)):

        start_time = '2021-01-28 00:00:00'
        end_time = '2021-01-30 23:59:59'
        one = kpi_data[kpi_data['tc'] == kpi_names[i]]
        dt_list, timestamp_list  = generate_time_list(start_time, end_time, 60)
        data_merge = padding_ts(dt_list, timestamp_list, one)
        data_merge = data_merge.fillna(-1)

        for _type in types:
            ts = [i if i != -1  else None for i in list(data_merge[_type])]
            n_upper, n_lower, stds= exe.run(ts)

            stds = [round(i,1) for i in stds]
            statistic_obj = StatisticMetric(
                is_valid = True,
                instance = kpi_names[i],
                instance_type = _type,
                n_upper = n_upper,
                n_lower = n_lower,
                std = json.dumps(stds)
                )
            statistic_obj.save()
            print(i)
