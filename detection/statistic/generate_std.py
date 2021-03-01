""" Standard Deviation
    by wzf

    Drop some points

    One point contribution:
    xN/std       var'/var
      3.8    -→    1.01
      6.5    -→    1.03
      8.5    -→    1.05
      12     -→    1.1
      17     -→    1.2

"""

import numpy as np
from copy import deepcopy
from detection.statistic.lowpass import low_pass_filter_batch

BUTTER_LPF_ORDER = 4
BUTTER_LPF_FREQZ = 0.03
BUTTER_LPF_FREQZ_DROP = 0.01
EPSILON = 0.0001
MIN_LENGTH = 20


class ErrorStandardDeviation(object):
    """ Drop some points, then calculate Std

    """


    def __init__(self, x, contirbution_ratio=0.03, complete_ratio=0.95):
        """ Init
        """

        self.x = [i for i in x if i is not None]
        self.contirbution_ratio = contirbution_ratio
        self.complete_ratio = complete_ratio

        if len(self.x) < MIN_LENGTH:
            raise RuntimeError('Calc std: x must be least 20 points')


    def calculate_error_standard(self):
        """ Calc std after drop points
            Std for err 
        """

        x = deepcopy(self.x)
        length = len(x)
        drop_index = []
        index_prime = list(range(length))    #prime index list

        while True:

            _, err = low_pass_filter_batch(x, N=BUTTER_LPF_ORDER, Wc=BUTTER_LPF_FREQZ_DROP)
            err = [i if abs(i) > EPSILON else 0 for i in err]
            _mean = np.mean(err)
            _std = np.std(err)

            if _std < EPSILON:    #If _std very small, maybe entropy of ts is very small
                return _std, []

            # turn contirbution ratio to N sigma
            n_sigma = np.sqrt(self.contirbution_ratio*length)
            del_index = [i for i in range(len(err)) if abs(err[i]-_mean)/_std > n_sigma]

            # Delete some points
            if del_index == [] or len(x) < length * self.complete_ratio:
                break
            else:
                x = [x[i] for i in range(len(err)) if i not in del_index]
                del_index = [index_prime[i] for i in del_index]
                drop_index += del_index
                index_prime = [i for i in index_prime if i not in del_index]
        if len(x) < MIN_LENGTH:
            return np.std(err), drop_index
        _, err_ = low_pass_filter_batch(x, N=BUTTER_LPF_ORDER, Wc=BUTTER_LPF_FREQZ)

        return np.std(err_), drop_index


    def run(self):
        """ Running
        """

        self.std, self.drop_index = self.calculate_error_standard()
        return self.std, self.drop_index