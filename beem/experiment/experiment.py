import numpy as np
import warnings
class Experiment(object):
    """Class to store general data about an experiment

    """

    def __init__(self, pos_x = None, pos_y = None, sample = None, 
            device = None, date = None, src_files = None):
        """Store general data

        Kwargs:
            pos_x (float): position x
            pos_y (float): position y
            sample (str): name of the sample
            device (str): name of the device (e.g.: 'C3')
            date (datetime): date and time of the experiment
            src_file (str): file used to store the raw data

        """
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.sample = sample
        self.device = device
        self.date = date
        self.src_files = src_files



_use_pure_c=True
bell_kaiser_v=None
residu_bell_kaiser_v=None

def use_pure_c(val=True):
    global bell_kaiser_v,residu_bell_kaiser_v,_use_pure_c
    if val==True:
        try:
            bell_kaiser_v=_pure_c.bell_kaiser_v
            residu_bell_kaiser_v=_pure_c.residu_bell_kaiser_v
            _use_pure_c = True
            return
        except:
            pass
    
    warnings.warn('Python code used instead of C code: slower')
    from . import _pure_python as _pure_python
    bell_kaiser_v = _pure_python.bell_kaiser_v
    residu_bell_kaiser_v = _pure_python.residu_bell_kaiser_v
    _use_pure_c = False


try:
  from . import _pure_c as _pure_c
  use_pure_c(True)
except ImportError:
  use_pure_c(False)
  
MODE = {'fwd':0, 'bwd':1} #Enum to store if in the foward or backward mode
BEEM_MODEL = {'bkv':0,'bk':1}

def r_squared(y_sampled, y_estimated):
    """Give the correlation coefficient between sampled data eand estimate data

    Args:
        y_sampled (ndarray): data sampled
        y_estimated (ndarray): data estimated by fitting

    Returns:
        float. squared correlation coefficient
    """
    if y_estimated==None:
        return np.NAN
    sse = sum( (y_sampled - y_estimated)**2 )
    sst = sum( (y_sampled - np.mean(y_sampled) )**2 )
    return 1 - sse / sst
