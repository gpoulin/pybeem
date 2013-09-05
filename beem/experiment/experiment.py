class Experiment(object):
    """Class to store general data about an experiment

    """

    def __init__(self, pos_x = None, pos_y = None, sample = None, 
            device = None, date = None, src_file = None):
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
        self.src_file = src_file

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
