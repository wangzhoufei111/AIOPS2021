""" 生成StatisticMetirc表
"""


import json
import numpy as np
import pandas as pd
from tqdm import tqdm
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
        from detection.scripts.generate_performance_statistic import run
    """

    kpi_paths = ['metric_0128.csv', 'metric_0129.csv', 'metric_0130.csv']
    kpi_data = pd.DataFrame()
    for path in kpi_paths:
        d = pd.read_csv(path, encoding='gb18030')
        kpi_data = kpi_data.append(d)

    start_time = '2021-01-28 00:00:00'
    end_time = '2021-01-30 23:59:59'
    dt_list, timestamp_list  = generate_time_list(start_time, end_time, 60)

    exe = GeneratorStandardNsigma()
    cmdb_ids = list(set(kpi_data['cmdb_id']))
    for cmdb_id in cmdb_ids:
        peers = kpi_data[kpi_data['cmdb_id'] == cmdb_id]
        names = list(set(peers['kpi_name']))
        for i in tqdm(range(len(names))):
            name = names[i]
            one = peers[peers['kpi_name'] == name]
            data_merge = padding_ts(dt_list, timestamp_list, one)
            data_merge = data_merge.fillna(-1)
            ts = [i if i != -1  else None for i in list(data_merge['value'])]

            n_upper, n_lower, stds = exe.run(ts)
            stds = [round(i,1) for i in stds]
            statistic_obj = StatisticMetric(
                is_valid = True,
                instance = name,
                instance_type = cmdb_id,
                n_upper = n_upper,
                n_lower = n_lower,
                std = json.dumps(stds)
                )
            statistic_obj.save()
