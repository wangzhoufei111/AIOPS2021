""" EMA算法
"""

import copy
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from scipy.signal.signaltools import (
    _validate_pad,
    axis_reverse, 
    axis_slice,
    )
from detection.algorithm.status_machine import StatusMachine
from detection.statistic.lowpass import low_pass_filter_batch

NORM_SIGMA_UPPER = 6
NORM_SIGMA_LOWER = 6
BUTTER_LPF_FREQZ = 0.04

ALPHA = 0.86
LEAST_POINTS = 10
CACL_SIGMA_UPPER = 0.95
CACL_SIGMA_LOWER = 0.05
STD_THRESHORLD = 1


class RegressionBase(object):

    """
        Regression algorithms base class
    """

    def __init__(self, **kwargs):
        """ Init
        """
        # Paramters
        self.name = None
        self.bounder = kwargs.get('bounder', 'both')
        self.sigma_upper = float(kwargs.get('sigma_upper', NORM_SIGMA_UPPER))
        self.sigma_lower = float(kwargs.get('sigma_lower', NORM_SIGMA_LOWER))
        # Data settings
        self.x_t = kwargs.get('x_t', None)
        self.std = kwargs.get('std', None)
        # minimun std
        # revise final std and bounder
        self.belt = kwargs.get('belt', None)
        self.wc = kwargs.get('wc') if kwargs.get('wc') else BUTTER_LPF_FREQZ
        self.wc = float(self.wc)
        self.y_t, self.s_t = None, None
        self.length = None
        self.label = None
        # Rules description
        self.rules = kwargs.get('rules', [])
        self.prior_status = kwargs.get('prior_status', None)
        # Pre alert status
        # self.pre_alert_status = kwargs.get('pre_alert_status', 'normal')


class ExponentialMovingAverage(RegressionBase):

    """
        Exponential moving average

        Example:
        ---------------------------------
        x = np.linspace(0, 1, 200)
        x = 2 * np.sin(np.pi * x)
        n = np.random.normal(0, 1, 200)
        x = x + n
        ema = ExponentialMovingAverage(x)
        ema.plot()
    """

    def __init__(self, x_t, y_t_1=None, std=None, is_iter=False, bounder='both', wc=None,
        sigma_upper=NORM_SIGMA_UPPER, sigma_lower=NORM_SIGMA_LOWER, alpha=ALPHA, rules=[], stds=[], **kargs):
        """ Init
        """
        # Paramters
        self.alpha = float(alpha)
        self.is_iter = is_iter
        super(ExponentialMovingAverage, self).__init__(x_t=x_t, y_t_1=y_t_1, std=std, wc=wc,
            bounder=bounder, sigma_upper=sigma_upper, sigma_lower=sigma_lower, rules=rules, **kargs)
        self.name = 'EMA'
        self.category = 'Regression'
        self.stds = _validate_pad('even', None, np.array(stds), -1, ntaps=LEAST_POINTS//3)[1]
        # Checking data
        if not self.is_iter:
            self.x_t = np.array(self.x_t)
            self.length = len(self.x_t)
            if self.x_t.ndim != 1:
                raise RuntimeError('series must be 1D')
            if self.length < LEAST_POINTS:
                raise RuntimeError('series length must larger than %s' % LEAST_POINTS)
        else:
            if self.x_t is None or self.y_t_1 is None or self.std is None:
                raise RuntimeError('x && y && std can not be None!')
            # Change x/y format to be array
            self.x_t, self.y_t_1 = np.array(self.x_t), np.array(self.y_t_1)
            if not self.x_t.shape:
                self.x_t = np.array([self.x_t])
            if not self.y_t_1.shape:
                self.y_t_1 = np.array([self.y_t_1])


    def run(self):
        """ Main method
        """
        if not self.is_iter:
            self.y_t, self.label = self.batch_filter()
        else:
            self.y_t, self.label = self.iter_filter()

        return self.y_t, self.label


    def __pre_processing(self):
        """ Pre-processing
            Estimate std && padding x
        """
        x, _L = copy.deepcopy(self.x_t), self.length
        self.s_t, err = low_pass_filter_batch(x, Wc=self.wc)
        _dc = copy.deepcopy(list(err))
        _dc.sort()
        self.std = np.std(_dc[int(np.ceil(CACL_SIGMA_LOWER * _L)): int(CACL_SIGMA_UPPER * _L)])
        self.std = self.std if self.std >= STD_THRESHORLD else STD_THRESHORLD
        print('>>> Pre std::', self.std)
        # Padding x for MA filter
        return _validate_pad('even', None, x, -1, ntaps=LEAST_POINTS//3)


    def __lfilter(self, x, prior_status='normal', during=0, direction='forward'):
        """ Filtering && Calculating base line
            prior_status :: important paramter for starting point 
        """
        # _L, std, alpha = len(x), self.std, self.alpha
        _L, alpha = len(x), self.alpha
        sigma_upper, sigma_lower = self.sigma_upper, self.sigma_lower
        y = [0] * _L
        status = []
        # Init y[0]
        y[0] = x[0]
        status.append([None, during, prior_status, None, None])
        # Filtering
        anomaly_status_machine = StatusMachine()
        for i in range(1, _L):
            # Last loop alert status
            if self.stds != []:
                std = self.stds[i]
            else:
                std = self.std
            _prerior_status = status[-1][2]
            is_outlier = (x[i] - y[i-1] >= sigma_upper * std) or \
                (y[i-1] - x[i] >= sigma_lower * std)
            # Alert status first
            if _prerior_status in ['smoking', 'opened', 'lasting',] or is_outlier:
                # lasy update
                y[i] = y[i-1]
            else:
                # update
                y[i] = alpha * y[i-1] + (1 - alpha) * x[i]
            # Update anomaly status machine
            anomaly_status_machine.set(
                is_outlier = is_outlier,
                during = status[-1][1],
                prior_status = status[-1][2],
                prior_alert_id = None
                )
            status.append(list(anomaly_status_machine.run()))

        return np.array(y), np.array(status)


    def __pro_processing(self):
        """ Backward filtering
            Recalculate standard
            Return labels
        """
        _B, _UT, _LT = self.bounder, self.sigma_upper * self.std, self.sigma_lower * self.std
        f = lambda x: 1 if (x[0] - x[1] >= _UT and _B in ['both', 'upper']) else \
            (2 if (x[1] - x[0] >= _LT and _B in ['both', 'lower']) else 0)
        # Return labels
        labels = np.array(list(map(f, zip(self.x_t, self.y_t_))))
        x_ = [self.x_t[i] for i in range(self.length) if labels[i]==0]
        # Re compare standard
        # _std = np.std(x_) if len(x_) else self.std
        # self.std = _std if _std < self.std else self.std
        # self.std = self.std if self.std >= STD_THRESHORLD else STD_THRESHORLD
        print('>>> Pro std::', self.std)

        return labels


    def batch_filter(self):
        """ EMA for batch
        """
        # Pre processing
        edge, ext = self.__pre_processing()
        # Forward filter
        prior_status = self.prior_status if self.prior_status else 'normal'
        during = 0
        y, status = self.__lfilter(
            ext, prior_status, during, direction='forward')
        self._y_t = axis_slice(y, start=edge, stop=-edge, axis=-1)
        # Backward filter
        # prior_status :: very important paramter
        # !! important & important & important
        prior_status = status[-1][2]
        during = 0
        y, _ = self.__lfilter(
            axis_reverse(y, -1), prior_status, during, direction='backward')
        # Reverse y
        y = axis_reverse(y, -1)
        self.y_t_ = axis_slice(y, start=edge, stop=-edge, axis=-1)
        # Pro processing
        self.label = self.__pro_processing()
        # Smoothing
        self.y_t, _ = low_pass_filter_batch(self.y_t_, Wc=self.wc)

        return self.y_t, self.label


    def iter_filter(self):
        """ EMA for iteration
        """
        x, y_t_1, std = self.x_t[0], self.y_t_1[0], self.std
        bounder, alpha = self.bounder, self.alpha
        sigma_upper, sigma_lower = self.sigma_upper, self.sigma_lower
        # Filtering
        if x - y_t_1 >= sigma_upper * std:
            # lasy update
            y = y_t_1
            if bounder == 'both' or bounder == 'upper':
                label = 1
            else:
                label = 0
        elif y_t_1 - x >= sigma_lower * std:
            # lasy update
            y = y_t_1
            if bounder == 'both' or bounder == 'lower':
                label = 2
            else:
                label = 0
        else:
            y = alpha * y_t_1 + (1 - alpha) * x
        self.y_t, self.label = np.array([y]), np.array([label])

        return self.y_t, self.label


    def plot(self):
        """ Plot result
        """
        if self.is_iter:
            print('>>> iter==True is not supported!')
            return
        # if not self.y_t:
        self.run()
        # Plot
        _upper_th = self.y_t + self.sigma_upper * self.std
        _lower_th = self.y_t - self.sigma_lower * self.std
        index = range(self.length)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(index, self.x_t, 'g', label='x(t)')
        ax.plot(index, self.y_t, 'b', label='EMA')
        ax.plot(index, self._y_t, 'orange', label='->EMA')
        ax.plot(index, self.y_t_, 'deeppink', label='EMA->')
        ax.plot(index, _upper_th, 'r--', label=r'+%s $\sigma$' % self.sigma_upper)
        ax.plot(index, _lower_th, 'r--', label=r'—%s $\sigma$' % self.sigma_lower)
        # If pass butterworth filter
        if not self.s_t is None:
            ax.plot(index, self.s_t, 'k', label='IIR-LPF')
        # Mark outlier points
        for i, v in enumerate(list(self.label)):
            if v:
                plt.scatter(i, self.x_t[i], color='r')
        plt.title('Exponential Moving Average', fontsize=18)
        plt.tick_params(labelsize=14)
        plt.legend(loc='upper right', fontsize=16)
        plt.axis('tight')
        plt.grid(True)

        plt.show()