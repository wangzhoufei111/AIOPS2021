""" Detecter
    风险事件输入模块
    Input: ts、instance、instance_type
           ts:[[timestamp1, v1], [timestamp2, v2], ...]
    Output: 风险事件，存储在RiskEvent表中
"""

import json
import numpy as np
import pandas as pd

from detection.algorithm.ema import ExponentialMovingAverage
from detection.models import (
    Rule,
    StatisticMetric,
    RiskEvent
    )

class Detecter(object):
    """ Detecter...
        Example:
        ---------------------------------
        from detection.detecter import Detecter
        exe = Detecter()
    """

    def __init__(self, ts, instance, instance_type):
        """ Init
        """

        self.ts = ts
        self.instance = instance
        self.instance_type = instance_type
        self.is_ready = True
        self.__load_rule()
        self.__load_statistic()


    def __load_rule(self):
        """ Load Rule
        """

        rule_objs = Rule.objects.filter(
            is_valid = True,
            instance = self.instance,
            instance_type = self.instance_type
            )
        if rule_objs:
            rule_obj = rule_objs[0]
            self.tag = rule_obj.tag
            self.cmdb_id = rule_obj.cmdb_id
            self.period = rule_obj.period
            self.alert_level = rule_obj.alert_level
            self.rule_values = rule_obj.values
        else:
            self.is_ready = False
        return None


    def __load_statistic(self):
        """ Load Statistic
        """

        statistic_objs = StatisticMetric.objects.filter(
            instance = self.instance,
            instance_type = self.instance_type
            )
        if statistic_objs:
            statistic_obj = statistic_objs[0]
            self.n_upper = statistic_obj.n_upper
            self.n_lower = statistic_obj.n_lower
            self.stds = json.loads(statistic_obj.std)
            print(self.n_upper, self.n_lower, self.stds)
        else:
            self.is_ready = False
        return None


    def run(self):
        """ Running
        """

        if self.is_ready:
            x = []
            stds_list = []
            for peer in self.ts:
                x.append(peer[1])
                stds_list.append(self.stds[int(peer[0][11:13])])
            print(stds_list)
            exe = ExponentialMovingAverage(x, sigma_upper=self.n_upper, sigma_lower=self.n_lower, stds=stds_list)
            exe.plot()

        else:
            print('Detecter is not ready!')

        pass


    def write_risk_events(self):
        """ Write to risk events
        """

        pass