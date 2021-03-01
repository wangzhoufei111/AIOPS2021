"""
    N - Sigma
    ```
                        ^                     
                      **|**                      
                   **** | ****                       
                  ***   |   ***                 
                ***     |     ***                   
            *  **       |        ** *
        —————————————————————————————————>
    ```
    @99.5% to detect anomaly
"""

import numpy as np 
from detection.statistic.entropy import EntropyAnalysis
from detection.statistic.lowpass import low_pass_filter_batch

BUTTER_LPF_ORDER = 4
BUTTER_LPF_FREQZ = 0.03
BUTTER_LPF_FREQZ_DROP = 0.01
IQR_R = 3
EPSILON = 0.0001
UPPER_LOWER_RATIO = [0.5,2]    #min_n cannot < 3(6*0.5)


class NSigma(object):
    """ Statistic N-sigma depend on anomaly-rate
    """

    def __init__(self, x, different_ratio_threshold=0.05, anomaly_ratio=0.005, bins=64, max_n=16, default_n=3.0):
        """ Init
            Separate x to bins , bin_interval = std/(bins/max_n/2)   default: 0.5*std
            by wzf
        """

        self.x = [i for i in x if i is not None]
        self.different_ratio_threshold = different_ratio_threshold
        self.anomaly_ratio = anomaly_ratio
        self.bins = bins
        self.max_n = max_n
        self.default_n = default_n

        if self.bins == 0:
            raise RuntimeError('Calc Nsigma: bins must be least 1')
        if len(x) < 100:    #<100 ？
            # If x is linear, lowpass will not be meet
            ### Need improve
            raise RuntimeError('Calc Nsigma: x must be least 100 points')


    def entropy_filter(self):
        """ Entropy Sift
        """

        entropy_analysis = EntropyAnalysis()
        en = entropy_analysis.ts_entropy(self.x)
        en_threshold = entropy_analysis.entropy_threshold(self.x, self.different_ratio_threshold)

        if en < en_threshold:
            # Low Entropy
            return True
        else:
            return False


    def box_filter(self, series, iqr_r=3):
        """ return point in [Q1-3*IQR, Q3+3*IQR]
        """

        Q1 = np.percentile(series, 25)
        Q3 = np.percentile(series, 75)
        IQR = Q3 - Q1
        lower = Q1 - iqr_r * IQR
        upper = Q3 + iqr_r * IQR
        box_series = [i for i in series if i<=upper and i>=lower]
        return box_series


    def square_mean(self, series):
        """ combine small std && big(prime) std
            mean: (n1 + n2 + ...)/N
            square_mean: np.sqrt((n1**2 + n2**2 + ...)/N)  
            reconcile_mean: N/(1/n1 + 1/n2 + ...)
            mean > square_mean > reconcile_mean
        """

        if not series:
            return EPSILON

        s = 0
        for value in series:
            s += value**2
        return np.sqrt(s/len(series))


    def cut_off_standard(self):
        """ When calculate std, need drop some points which are far from max_n*std
        """

        _, err = low_pass_filter_batch(self.x, N=BUTTER_LPF_ORDER, Wc=BUTTER_LPF_FREQZ)
        err = [i if abs(i) > 1e-5 else 0 for i in err]    #compensate some low-entropy ts
        box_err = self.box_filter(err, iqr_r=IQR_R)
        std_err = np.std(err)
        std_box = np.std(box_err)
        std_geometry = self.square_mean([std_err, std_box])

        # Dorp points index (>max_n*std)
        drop_index = [i for i in range(len(err)) if err[i] > self.max_n*std_geometry]

        x_ = [self.x[i] for i in range(len(self.x)) if i not in drop_index]
        _, err_ = low_pass_filter_batch(x_, N=BUTTER_LPF_ORDER, Wc=BUTTER_LPF_FREQZ)
        box_err_ = self.box_filter(err_, iqr_r=IQR_R)
        std_err_ = np.std(err_)
        std_box_ = np.std(box_err_)
        cutoff_std = self.square_mean([std_err_, std_box_])

        return err_, cutoff_std


    def probability_density_distribution(self):
        """ PDF, Even symmetry
        """

        l = len(self.err)
        pdf = [0] * self.bins           #init pdf, length of pdf = bins + 2
        half = int(self.bins/2)         #left or right bins length
        ratio = self.max_n * 2 / self.bins
        width = ratio * self.std        #bins width

        for i in range(-half, half):
            amount = len([p for p in self.err if p>=i*width and p<(i+1)*width])
            pdf[i+half] = amount / l
        # Padding in order to fill sum=1
        _edge = len([p for p in self.err if p < -half*width]) / l
        edge_ = len([p for p in self.err if p >= half*width]) / l
        pdf_whole = [_edge] + pdf + [edge_]    #bins/2 + 2

        # If points centerate edges, N is default_n
        complete_ratio = 1 - _edge - edge_
        if complete_ratio == 0:
            return self.max_n, self.max_n

        n_lower, n_upper = self.default_n, self.default_n
        # Right N
        s = 0
        for i_r in range(half):
            s += pdf[self.bins-1-i_r]
            if s/complete_ratio >= self.anomaly_ratio:
                n_upper = half - i_r + 1
                break
        n_upper = n_upper * ratio
        # Left N
        s = 0
        for i_l in range(half):
            s += pdf[i_l]
            if s/complete_ratio >= self.anomaly_ratio:
                n_lower = i_l - half - 1
                break
        n_lower = abs(n_lower * ratio)

        # upper and lower not the same like 6sigma  lower_upper_ratio ~~ [0.5,2](default_n >= 3)
        lower_upper_ratio = 1.0 if n_upper==0 else n_lower / n_upper
        lower_upper_ratio = UPPER_LOWER_RATIO[0] if lower_upper_ratio < UPPER_LOWER_RATIO[0] else lower_upper_ratio
        lower_upper_ratio = UPPER_LOWER_RATIO[1] if lower_upper_ratio > UPPER_LOWER_RATIO[1] else lower_upper_ratio
        if n_upper < self.default_n:
            n_upper = self.default_n / lower_upper_ratio if lower_upper_ratio > 1 else self.default_n
        if n_lower < self.default_n:
            n_lower = self.default_n * lower_upper_ratio if lower_upper_ratio < 1 else self.default_n

        return n_upper, n_lower


    def run(self):
        """ Running
        """

        # if x is low entropy ,left_N and right_N are both default_n
        if self.entropy_filter():
            return self.default_n, self.default_n, 'low_entropy'

        # self.x_ after self.x drop some points(very little maybe 1 or 2 point)
        self.err, self.std = self.cut_off_standard()

        # Calculate N through pdf
        n_upper, n_lower = self.probability_density_distribution()

        return n_upper, n_lower, 'high_entropy'