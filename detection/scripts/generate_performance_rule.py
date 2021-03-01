""" 生成Rule配置性能类型的
"""

import json
import pandas as pd
from detection.models import Rule


def run():
    """ from detection.scripts.generate_performance_rule import run
    """

    kpi_paths = ['metric_0128.csv', 'metric_0129.csv', 'metric_0130.csv']
    kpi_data = pd.DataFrame()
    for path in kpi_paths:
        d = pd.read_csv(path, encoding='gb18030')
        kpi_data = kpi_data.append(d)

    cmdb_ids = list(set(kpi_data['cmdb_id']))
    for cmdb_id in cmdb_ids:
        peers = kpi_data[kpi_data['cmdb_id'] == cmdb_id]
        names = list(set(peers['kpi_name']))
        for name in names:
            v = {"upper": 6.0, "lower": 6.0, "belt": 1.0, "bounder": "both", "dtype": "dynamic", "times": 3}
            rule_obj = Rule(
                is_valid = True,
                tag = 'performance',
                instance = name,
                instance_type = cmdb_id,
                cmdb_id = cmdb_id,
                period = 60,
                alert_level = 'P1',
                values = json.dumps(v)
                )
            rule_obj.save()
