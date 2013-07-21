"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""

import numpy as np
import scipy.optimize as op
import multiprocessing as mp

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



class Experiment(object):
    """Class to store general data about an experiment

    """

    def __init__(self, pos_x = None, pos_y = None, sample = None, device = None,
                 date = None, src_file = None):
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

class Grid(Experiment):

    def __init__(self,**kwd):
        super(Grid,self).__init__(**kwd)
        self.size_x = None
        self.size_y = None
        self.num_x = None
        self.num_y = None
        self.num_pass=None
        self.num_sweep=None
        self.bees = []
        self.beesfit = []
        self.completed=False
        self.xs=[]
        self.ys=[]
        self.bees_dict=None
        self.beesfit_dict=dict()

    def __add__(self,other):
        ret=Grid()
        ret.bees=self.bees+other.bees
        ret.beesfit=self.beesfit+other.beesfit
        return ret

    def normal_fit(self):
        self.beesfit=[BEESFit(self.bees[i]) for i in range(len(self.bees))]
        for b in self.beesfit:
            b.set_id()
            self.beesfit_dict[b.id]=b
            b.parent=self

    def set_n(self,n):
        for b in self.beesfit:
            b.n=n


    def fit(self,threads=1):
        from time import time
        t1=time()
        if threads==1:
            for x in self.beesfit:
                x.fit_update()
        else:
            if threads==-1:
                p=mp.Pool()
            else:
                p=mp.Pool(threads)
            beesfit=p.map(fit_para,self.beesfit)
            p.close()
            for i in range(len(beesfit)):
                self.beesfit[i].update(beesfit[i])
        t2=time()
        print(t2-t1)

    def set_coord(self):
        self.xs = np.unique(filter(lambda x: not(x==None),
                            [b.pos_x for b in self.bees]))
        self.ys = np.unique(filter(lambda x: not(x==None),
                            [b.pos_y for b in self.bees]))

    def set_indexes(self):
        x_len=np.array(range(len(self.xs)))
        y_len=np.array(range(len(self.ys)))
        for b in self.bees:
            b.x_index=x_len[self.xs==b.pos_x][0]
            b.y_index=y_len[self.ys==b.pos_y][0]

    def set_pass_number(self):
        dic=dict()
        for b in self.bees:
            b.pass_number=1
            b.set_id()
            if b.id in dic:
                dic[b.id].append(b)
            else:
                dic[b.id]=[b]

        for l in dic.values():
            if len(l)==1:
                pass
            else:
                l.sort(key=lambda x:x.date)
                for i in range(2,len(l)):
                    l[i].pass_number=i

    def init_grid(self):
        self.set_coord()
        self.set_indexes()
        self.set_pass_number()
        self.num_x=len(self.xs)
        self.num_y=len(self.ys)
        self.num_sweep=max([x.number for x in self.bees])
        self.num_pass=max([x.pass_number for x in self.bees])
        self.bees_dict=dict()
        for b in self.bees:
            b.set_id()
            self.bees_dict[b.id]=b
            b.parent=self

    def update_dict(self):
        self.init_grid()
        self.beesfit_dict=dict()
        for b in self.beesfit:
            b.set_id()
            b.parent=self
            self.beesfit_dict[b.id]=b


    def extract_good(self,r_squared=0.6):
        fit=np.array(self.beesfit)
        r=np.array([x.r_squared for x in fit])
        return fit[np.logical_and(r>r_squared,r<1)]

def fit_para(x):
    return x.fit()


class IV(Experiment):

    def __init__(self,**kwd):
        super(IV,self).__init__(**kwd)
        self.V=np.array([])
        self.I=np.array([])
        self.mode=MODE['fwd']
        self.T=300.0
        self.A=1.1e6
        self.W=np.pi*2.5e-4**2
        self.n=0
        self.barrier_height=0
        self.r_squared=0
        self.Vmax=0
        self.Vmin=0
        self.KbT=constants.physical_constants['Boltzmann constant in eV/K'][0]\
                *self.T
        self.Is=self.A*self.W*self.T**2

    @property
    def _fit_index(self):
        return np.logical_and(self.V<self.Vmax,self.V>self.Vmin)

    @property
    def V_fitted(self):
        return self.V[self._fit_index]

    @property
    def I_fitted(self):
        return self.I[self._fit_index]

    @staticmethod
    def schottky_richardson(V,Vbh,n,Is,KbT):
        I=Is*np.exp(-Vbh/(KbT)+V/(n*KbT))*(1-np.exp(-V/(KbT)))
        return I

    def _model_fit(self,V,Vbh,n):
        return np.log(np.abs(IV.schottky_richardson(V,Vbh,n,self.Is,self.KbT)))

    def fit(self,Vbh_init=0.8,n_init=1.0):
        popt,pconv=op.curve_fit(self._model_fit,self.V_fitted,
                np.log(np.abs(self.I_fitted)),[Vbh_init,n_init])
        self.barrier_height=popt[0]
        self.n=popt[1]
        self.r_squared=r_squared(np.log(np.abs(self.I_fitted)),
                self._model_fit(self.V_fitted,popt[0],popt[1]))


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
