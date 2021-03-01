# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 17:39:43 2019

@author: zhoufeiwang
"""

import datetime


class StatusMachine(object):

    """Alert status machine migration:
       Alert status: [`smoking`, `open`, `lasting`, `closed`, `normal`, `layoff`]
    """

    STATUS = ['smoking', 'opened', 'lasting', 'closed', 'normal', 'layoff']

    def __init__(self, 
        produce_intervel=3, 
        recovery_intervel=3, 
        notify_intervel=None, by_pass_smoking=False, detection_id=''):
        """ Init
            produce_intervel: 
                times of concerting anomaly to alert, 
                `smoking` to `opened`
            recovery_intervel: 
                times of concerting anomaly to alert, 
                `layoff` to `closed`
            notify_intervel: 
                times of concerting anomaly to alert, 
                notify interval during alert `lasting`
        """
        self.produce_intervel = produce_intervel
        self.recovery_intervel = recovery_intervel
        self.notify_intervel = notify_intervel
        self.by_pass_smoking = by_pass_smoking
        self.detection_id = str(detection_id)
        self.date_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')


    def set(self, is_outlier, during=0, prior_status=None, prior_alert_id=''):
        """ is_outlier: current alert status
            prior_status: prior alert status
            during: from `opened` 
        """
        if prior_status and not prior_status in self.STATUS:
            raise RuntimeError('Alert status: \
                [`smoking`, `open`, `lasting`, `closed`, `normal`, `layoff`]')
        self.during = during
        self.is_outlier = is_outlier
        self.prior_status = prior_status
        self.prior_alert_id = prior_alert_id if prior_alert_id else ''
        self.cur_status = None
        self.notify_status = False
        self.alert_status = False
        self.cur_alert_id = self.prior_alert_id
        

    def __migrate(self):
        """ Generate current alert status && during times
        """
        # `normal` 2 `normal`
        if self.prior_status == 'normal' and not self.is_outlier:
            self.cur_status = 'normal'
            self.during += 1

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `normal` 2 `smoking` && `opened`
        if self.prior_status == 'normal' and self.is_outlier:
            if self.by_pass_smoking or self.produce_intervel == 1:
                self.cur_status = 'opened'
                self.during = 1
                # Alert notify status
                self.alert_status = self.notify_status = True
                # Generate new alert id
                self.cur_alert_id = '-'.join([self.detection_id, self.date_time])
            else:
                self.cur_status = 'smoking'
                self.during = 1

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `smoking` 2 `normal`
        if self.prior_status == 'smoking' and not self.is_outlier:
            self.cur_status = 'normal'
            self.during = 1

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `smoking` 2 `smoking` &&  `opened`
        if self.prior_status == 'smoking' and self.is_outlier:
            if (self.during + 1) >= self.produce_intervel:
                self.cur_status = 'opened'
                self.during = 1
                # Alert notify status
                self.alert_status = self.notify_status = True
                # Generate new alert id
                self.cur_alert_id = '-'.join([self.detection_id, self.date_time])
            else:
                self.cur_status = 'smoking'
                self.during += 1

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `opened` 2 `lasting`
        if self.prior_status == 'opened' and self.is_outlier:
            self.cur_status = 'lasting'
            self.during += 1
            self.alert_status = True

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `opened` 2 `layoff`
        if self.prior_status == 'opened' and not self.is_outlier:
            self.cur_status = 'layoff'
            self.during = 1
            self.alert_status = True

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `lasting` 2 `lasting`
        if self.prior_status == 'lasting' and self.is_outlier:
            self.cur_status = 'lasting'
            self.during += 1
            self.alert_status = True
            self.notify_status = not (self.during % self.notify_intervel) if \
                self.notify_intervel else False

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `lasting` 2 `layoff`
        if self.prior_status == 'lasting' and not self.is_outlier:
            self.cur_status = 'layoff'
            self.during = 1
            self.alert_status = True

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `layoff` 2 `lasting`
        if self.prior_status == 'layoff' and self.is_outlier:
            self.cur_status = 'lasting'
            self.during = 1
            self.alert_status = True

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `layoff` 2 `layoff` && `normal`
        if self.prior_status == 'layoff' and not self.is_outlier:
            if (self.during + 1) >= self.recovery_intervel:
                self.cur_status = 'closed'
                self.during = 1
                # Alert notify status
                self.notify_status = True
            else:
                self.cur_status = 'layoff'
                self.during += 1
                self.alert_status = True

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id
        # `closed` 2 `layoff` && `normal`
        if self.prior_status == 'closed':
            self.cur_status = 'normal' if not self.is_outlier else 'opened'
            self.during += 1
            # Alert notify status
            self.notify_status = True if self.cur_status == 'opened' else False
            self.alert_status = True if self.cur_status == 'opened' else False
            if self.notify_status:
                # Generate new alert id
                self.cur_alert_id = '-'.join([self.detection_id, self.date_time])
            else:
                self.cur_alert_id = ''

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id

        # `Prior status`
        if not self.prior_status:
            if self.is_outlier:
                self.cur_status = 'opened' if self.by_pass_smoking else 'smoking'
                self.during = 1
                # Alert notify status
                if self.by_pass_smoking:
                    self.notify_status = True
                    self.alert_status = True
                    self.cur_alert_id = '-'.join([self.detection_id, self.date_time])
            else:
                self.cur_status = 'normal'
                self.during = (self.during + 1) if isinstance(self.during, int) else 1

            return self.cur_status, self.during, \
                self.notify_status, self.alert_status, self.cur_alert_id


    def run(self):
        """ Call method
        """
        return self.__migrate()