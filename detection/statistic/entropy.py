""" @function: Entropy of Time Series
    ```
        Generate the entropy of cat time series:
        using the length of window: 64
        total entropy expected to be 6(64=2^6)
        ent = - xiga(p*log2(p))
    ```
"""
import math
import numpy as np
import pandas as pd
from scipy import stats

ENTROPY_WINDOW = 64
ENTROPY_ABS_SUBSTITUTE = 0
BUTTER_LPF_FREQZ = 0.08


class EntropyAnalysis(object):
    """ Three Entropy of TS (bit, log2)
    """

    def entropy_threshold(self, x, different_ratio_threshold=0.05):
        """ entropy-threshold
            different_ratio_threshold=0.05: It can tolerate totally different 500 points in 10000 points
        """

        if not x:
            raise RuntimeError('Calc entropy: x must not be none')
        l = len(x)
        toler_l = int(l * different_ratio_threshold)
        en_threshold = self.ts_entropy([-1]*(l-toler_l) + list(range(toler_l)))
        return en_threshold


    def ts_entropy(self, x):
        """ Prime Entropy of TS (log2)
        """

        if not x:
            raise RuntimeError('Calc entropy: x must not be none')
        probs = pd.Series(x).value_counts() /len(x)
        entropy_ln = stats.entropy(probs)
        entropy_log2 = np.log2(math.exp(entropy_ln))
        return entropy_log2


    def bins_entropy(self, x, bins):
        """ Bins Entropy of TS (log2)
        """

        if not x:
            raise RuntimeError('Calc entropy: x must not be none')
        _x_cut = pd.cut(x,bins)
        x_cut_ = pd.value_counts(_x_cut)
        x_cut = x_cut_.sort_index()

        distribution = np.array(x_cut) / sum(x_cut)
        entropy_log2 = 0.0
        for i in range(len(distribution)):
            p = distribution[i]
            if p == 0.0:
                continue
            entropy_log2 -= p * np.log2(p)
        return entropy_log2


    def approximate_entropy(self, x, m, r):
        
        pass
    

    def sample_entropy(self, x):
        
        pass