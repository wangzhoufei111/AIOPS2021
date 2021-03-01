import numpy as np
from scipy import signal

def low_pass_filter_batch(x, N=4, Wc=0.02):
    """
        Low pass filter of butterworth filter
        Filter order be signed to 3rd
        Normalize freq band between 0 ~ 0.1
    """
    b, a = signal.butter(N, Wc, 'low')
    y = signal.filtfilt(b, a, x)

    return y, np.array(x) - y