""" 生成Rule配置kpi类型的
"""

import json
import pandas as pd
from detection.models import Rule


def run():
    """ from detection.scripts.generate_kpi_rule import run
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
    for kpi in kpi_names:
        for type in types:

            v = {"upper": 6.0, "lower": 6.0, "belt": 1.0, "bounder": "both", "dtype": "dynamic", "times": 3}
            rule_obj = Rule(
                is_valid = True,
                tag = 'business',
                instance = kpi,
                instance_type = type,
                cmdb_id = '',
                period = 60,
                alert_level = 'P0',
                values = json.dumps(v)
                )

            rule_obj.save()