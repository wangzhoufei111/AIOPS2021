""" Generate std && N

    Standard Deviation

    Space-Time Dimension
    |----|----|----|---------  std'
    |----|----|----|---------  std'
    |----|----|----|---------  std'
    |----|...
     std1 std2 std3 ...
    
    std1' = f(std1,std')
    std2' = f(std2,std')
    ...

"""


import time
import datetime
import numpy as np
import pandas as pd
from detection.statistic.n_sigma import NSigma
from detection.statistic.generate_std import ErrorStandardDeviation
from detection.statistic.lowpass import low_pass_filter_batch

DIFFERENT_RATIO_THRESHOLD = 0.05    #熵值阈值
ANOMALY_RATIO = 0.005    #异常率
BINS = 64    #概率密度函数分bin个数
MAX_N = 16    #最大N限制
DEFAULT_N = 6.0    #默认N限制
EPSILON = 0.0001    #最小值
DROPOUT_SPAT_RATIO = 0.95    #空间std计算时候保留率
DROPOUT_TIMS_RATIO = 0.99    #时间std计算时候保留率
CONTRIBUTION_RATIO = 0.1    #丢点的贡献率
DEFAULT_STD = 1.0    #最低std值
BUTTER_LPF_ORDER = 4    #滤波器阶数
BUTTER_LPF_FREQZ = 0.1    #滤波器频率
BLANK_RATIO = 0.5    #时序占空比阈值


class GeneratorStandardNsigma(object):
    """ Nsigma
        Generator std && N

        Example:
        ---------------------------------
        x = np.linspace(0, 1, 200)
        x = 2 * np.sin(np.pi * x)
        n = np.random.normal(0, 1, 200)
        x = x + n
        resp = GeneratorStandardNsigma().run(x)
    """
    
    
    def __init__(self):
        """ Init
        """
        
        # N vailables
        self.sub_length = 1440   #Sample sequence length
        self.step = 60    #Sample step
        
        # Std vailables
        self.spat_window = 60
        self.spat_step = 60
    
    
    def valid_check(self, series, blank_ratio=BLANK_RATIO):
        """ Check t if have enough points
        """

        if not series:
            return None

        series_ = [i for i in series if i is not None]
        if len(series_) / len(series) >= blank_ratio:
            return series_
        else:
            return None
    
    
    def square_mean(self, series):
        """ combine small std && big(prime) std
            mean: (n1 + n2 + ...)/N
            square_mean: np.sqrt((n1**2 + n2**2 + ...)/N)  
            reconcile_mean: N/(1/n1 + 1/n2 + ...)
            square_mean >= mean > reconcile_mean
        """
        if not series:
            return EPSILON

        s = 0
        for value in series:
            s += value**2
        return np.sqrt(s/len(series))
    
    
    def calculate_n(self):
        """ Calculate N statistic
            Need 10 seconds
        """

        if len(self.x) < self.sub_length:
            raise RuntimeError('Calc N: x must be least {} points'.format(self.sub_length))

        sub_number = int((len(self.x)-self.sub_length)/self.step) + 1    #subsequnece number
        n_upper_list, n_lower_list = [], []
        for i in range(sub_number):
            # Not enough points of subsequence
            _sub_x = self.x[i*self.step: self.sub_length + i*self.step]
            sub_x = self.valid_check(_sub_x)
            if not sub_x or len(sub_x) <= 20:
                continue

            # Calculate N for subsequence
            nstd = NSigma(sub_x, 
                different_ratio_threshold = DIFFERENT_RATIO_THRESHOLD, 
                anomaly_ratio = ANOMALY_RATIO, 
                bins = BINS, 
                max_n = MAX_N,
                default_n = DEFAULT_N)
            _n_upper, _n_lower, _ = nstd.run()
            n_upper_list.append(_n_upper)
            n_lower_list.append(_n_lower)

        if n_upper_list==[] or n_lower_list==[]:  
            # Not enough points of samples
            self.n_upper, self.n_lower = DEFAULT_N, DEFAULT_N
        else:
            self.n_upper = self.square_mean(n_upper_list)
            self.n_lower = self.square_mean(n_lower_list)
        return
    
    
    def calculate_standard(self):
        """ Calculate Std
            Need 0.1 seconds
        """

        # Times aligned for subsequence
        tims_n = int(np.ceil(len(self.x)/self.sub_length))    #tims_n = 8
        tims_stds = []
        for i in range(tims_n):
            _tims_x = self.x[i*self.sub_length: (i+1)*self.sub_length]
            tims_x = self.valid_check(_tims_x)
            if not tims_x or len(tims_x) <= 20:
                continue
            std_, _ = ErrorStandardDeviation(tims_x, CONTRIBUTION_RATIO, DROPOUT_TIMS_RATIO).run()
            tims_stds.append(std_)

        if tims_stds:
            # EMA tims Std
            s = 0
            for j in range(len(tims_stds)):
                s += 2**j*tims_stds[j]
            tims_std = s/ sum([2**i for i in range(len(tims_stds))])
        else:
            tims_std = DEFAULT_STD

        # Spatially aligned for window
        spat_n = int(np.ceil(self.sub_length/self.spat_step))
        _spat_stds = []
        for col_i in range(spat_n):
            _combine_x = []
            # spatially window combine
            for row_i in range(tims_n):
                _combine_x += list(self.x[row_i*self.sub_length + col_i*self.spat_step: \
                                          row_i*self.sub_length + col_i*self.spat_step + self.spat_window])
            # Not enough points of window
            combine_x = self.valid_check(_combine_x)
            if not combine_x or len(combine_x) <= 20:
                try:
                    # First std lost
                    _std = _spat_stds[-1]
                except:
                    _std = tims_std
            else:
                _std, _ = ErrorStandardDeviation(combine_x, CONTRIBUTION_RATIO, DROPOUT_SPAT_RATIO).run()
            _spat_stds.append(_std)
        # Smoother _spat_stds
        _, drop_index = ErrorStandardDeviation(_spat_stds, CONTRIBUTION_RATIO, DROPOUT_SPAT_RATIO).run()
        _spat_stds = [_spat_stds[i] if i not in drop_index else np.nan for i in range(len(_spat_stds))]
        spat_stds_ = pd.Series(_spat_stds).interpolate(limit_direction = 'both')
        smoother_spat_stds, _ = low_pass_filter_batch(spat_stds_, N=BUTTER_LPF_ORDER, Wc=BUTTER_LPF_FREQZ)
        spat_stds = [smoother_spat_stds[i] if smoother_spat_stds[i] > EPSILON else spat_stds_[i] \
            for i in range(len(smoother_spat_stds))]

        stds = [(i+tims_std)/2 for i in spat_stds]
        return stds
    
    
    def wirte_back(self):
        """ Write back to db
        """
        
        pass
    
    
    def run(self, ts):
        """ Running
        """
        
        self.x = ts
        use_length = len([i for i in self.x if i])
        if len(self.x) < 1000:
            return DEFAULT_N, DEFAULT_N, DEFAULT_STD
        
        # Calculate N
        self.calculate_n()
        
        # Calculate Std
        stds = self.calculate_standard()
        
        self.stds = []
        for std in stds:
            if std < DEFAULT_STD:
                self.stds.append(DEFAULT_STD)
            else:
                self.stds.append(std)

        
        # Save to db
        self.wirte_back()
        
        return self.n_upper, self.n_lower, self.stds