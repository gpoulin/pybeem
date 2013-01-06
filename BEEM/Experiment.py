# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""

import numpy as np
import scipy.optimize as op
import pylab
import scipy.constants as constants

MODE = {'fwd':0, 'bwd':1} #Enum to store if in the foward or backward mode

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
        
class BEESData(Experiment):
    
    def __init__(self, bias = None, i_tunnel = None, i_beem = None, 
                 pos_z = None, mode = MODE['fwd'], number=1, **kwds):
        
        super(BEESData, self).__init__(**kwds)        
        self.bias = bias
        self.i_tunnel = i_tunnel
        self.i_beem = i_beem
        self.pos_z = pos_z
        self.mode = mode
        self.number = number
        
class BEESFit(object):
    
    def __init__(self,data=None):
        self.data = []
        self.add_data(data)
        self.filter = None #no filter
        self._i_beem = None
        self.trans_a = None
        self.trans_r = None
        self.barrier_height = None
        self.barrier_height_max=-0.5
        self.noise = None
        self.combine = lambda x: np.mean(x, 0)
        self.method = BEESFit.bell_kaiser_v
        self.bias_max=np.max(self.bias)
        self.bias_min=np.min(self.bias)
        self.updated = False
        
    @property
    def bias(self):
        
        if not(self.data):
            return None
        else:
            return self.data[0].bias
    
    @property
    def index(self):
        return  np.logical_and(self.bias < self.bias_max, 
                               self.bias > self.bias_min)
    
    @property
    def i_beem_fitted(self):
        return self.i_beem[self.index]
        
    @property
    def bias_fitted(self):
        return self.bias[self.index]
        
    @property
    def i_beem_estimated(self):
        if self.barrier_height==None:
            return None
        return self.method(self.bias_fitted, self.barrier_height, 
                           self.trans_a, self.noise);
    
    @property
    def pos_x(self):
        if not(self.data):
            return None
        
        pos_x = np.array([t.pos_x for t in self.data])
        if all(pos_x == pos_x[0]):
            return pos_x[0]
        else:
            return None
            
    @property
    def pos_y(self):
        if not(self.data):
            return None
        
        pos_x = np.array([t.pos_y for t in self.data])
        if all(pos_x == pos_x[0]):
            return pos_x[0]
        else:
            return None
    
    @property
    def i_beem(self):
        if not(self.data):
            return None
        
        if len(self.data)>1:
            combined=self.combine([t.i_beem for t in self.data])
        else:
            combined=self.data[0].i_beem
        
        if self.filter==None:
            self._i_beem=combined
        else:
            self._i_beem = self.filter(combined)
        return self._i_beem
    
    def reset(self):
        self._i_beem = None
        self.barrier_height = None
        self.trans_a = None
        self.trans_r = None
        self.noise = None
        self.updated = False
    
    def add_data(self, data):
        self.reset()
        if isinstance(data,BEESData):
            self.data.append(data)
        else:
            for bees in data:
                 self.data.append(bees)
    
    def fit(self, barrier_height = -0.8, trans_a = 0, noise = 1e-9):
        
        try:
            popt, pconv = op.curve_fit(self.method, self.bias_fitted, 
                                   self.i_beem_fitted, 
                                   [barrier_height, trans_a, noise])
        
                        
            self.barrier_height = popt[0]
            self.trans_a = popt[1]
            self.noise = popt[2]
        except:
            self.barrier_height = None
            self.trans_a = None
            self.noise = None            
            
        
    def export_plot(self,fig=1):
        pylab.figure(fig)
        pylab.plot(self.bias, self.i_beem,'.k')
        pylab.plot(self.bias_fitted,self.i_beem_estimated,'r')
        pylab.xlabel('Bias (V)')
        pylab.ylabel('BEEM Current (A)')
    
    def auto_range_fit(self, barrier_height = -0.8, trans_a = 1.0, 
                       noise = 1e-9, auto_range = 0.4, tol = 0.001):
        self.barrier_height = barrier_height
        self.trans_a = trans_a
        self.noise = noise
        
        for i in range(0,10):
            self.fit(self.barrier_height, self.trans_a, self.noise)
            if self.barrier_height==None:
                return
            if self.barrier_height>self.bias_max:
                self.barrier_height=self.bias_max            
            self.bias_min=(self.barrier_height+barrier_height)/2-auto_range
            if np.abs(barrier_height-self.barrier_height)<tol:
                return
            barrier_height=self.barrier_height
            
        
    @property
    def r_squared(self):
      return r_squared(self.i_beem_fitted,self.i_beem_estimated)
        
    
    @staticmethod
    def bell_kaiser_v(bias, barrier_height, trans_a, noise):
        i_beem = np.zeros(bias.shape[0])
        x=bias < barrier_height
        i_beem[x] = -trans_a*(bias[x] - barrier_height)**2  / bias[x]
        return i_beem + noise
    
    @staticmethod
    def bell_kaiser(bias, barrier_height, trans_a, noise):
        i_beem = np.ones(bias.shape[0]) * noise
        i_beem[bias < barrier_height] = (-trans_a * 
            (bias[bias < barrier_height] - barrier_height)**2 ) + noise
        return i_beem
    
class Grid(Experiment):
    
    def __init__(self,**kwd):
        super(Grid,self).__init__(**kwd)
        self.size_x = None
        self.size_y = None
        self.num_x = None
        self.num_y = None
        self.bees = []
        self.beesfit = []
        self.fit_method='auto_range_fit'
        self.completed=False
        
    def normal_fit(self):
        self.beesfit=[BEESFit(self.bees[i][j])
                    for i in range(0,len(self.bees)) 
                    for j in range(0,len(self.bees[i]))]
        
        for beesfit in self.beesfit:
            beesfit.auto_range_fit()
            #beesfit.__getattribute__(self.fit_method)()

class IV(Experiment):

    class model():
        SchottkyRicharson=0
    
    def __init__(self):
        self._fitted=[False,False]
        self.model=IV.model.SchottkyRicharson
        self._T=300.
        self._A=1.1e6
        self._W=np.pi*2.5e-4**2
        self._Vbh=[0.8,0.8]
        self._n=[1,1]        
        self._Vmax=[0.15,0.15]
        self._Vmin=[0.03,0.03]
        self._rsquared=[0,0]
        self._KbT=constants.physical_constants['Boltzmann constant in eV/K'][0]*self._T
        self._Is=self._A*self._W*self._T**2
        self.mode=MODE['fwd']
        self.filter=None

    @property
    def Vbh(self):
        if not(self._fitted[self.mode]):
            self.fit()   
        return self._Vbh[self.mode]
    
    @property
    def n(self):
        if not(self._fitted[self.mode]):
            self.fit()   
        return self._n[self.mode]
    
    @property
    def rsquared(self):
        if not(self._fitted[self.mode]):
            self.fit()   
        return self._rsquared[self.mode]

    @property
    def Vmax(self):
        return self._Vmax[self.mode]

    @property
    def Vmin(self):
        return self._Vmin[self.mode]
        
    @Vmax.setter
    def Vmax(self,value):
        self._Vmax[self.mode]=value
        self._fitted[self.mode]=False
    
    @Vmin.setter
    def Vmin(self,value):
        self._Vmin[self.mode]=value
        self._fitted[self.mode]=False
        
    @property
    def T(self):
        return self._T
        
    @T.setter
    def T(self,value):
        self._T=value
        self._fitted=[False,False]
        
    @property
    def A(self):
        return self._A
        
    @A.setter
    def A(self,value):
        self._A=value
        self._fitted=[False,False]
    
    @property
    def W(self):
        return self._W
        
    @W.setter
    def W(self,value):
        self._W=value
        self._fitted=[False,False]
    
    @property
    def V(self):
        return self._V[:,self.mode]
        
    @property
    def I(self):
        I=self._I[:,self.mode]
        if self.filter==None:
            return I
        else:
            return self.filter(I)

        
    def fit(self,Vbh_init=None,n_init=None):
        m=self.mode
        if Vbh_init==None:
            Vbh_init=self._Vbh[m]
        if n_init==None:
            n_init=1
            
        V=self.V[np.logical_and(self.V<self.Vmax,self.V>self.Vmin)]
        if V.size<2:
            return
        I=self.I[np.logical_and(self.V<self.Vmax,self.V>self.Vmin)]
        popt,pconv=op.curve_fit(self._model_fit,V,np.log(np.abs(I)),[Vbh_init,n_init])
        self._Vbh[m]=popt[0]
        self._n[m]=popt[1]
        self._rsquared[m]=r_squared(np.log(np.abs(I)),self._model_fit(V,popt[0],popt[1]))
        self._fitted[m]=True
        
    def _model_fit(self,V,Vbh,n):
        return np.log(np.abs(IV.schottky_richardson(V,Vbh,n,self._Is,self._KbT)))
        

    def Ifitted(self,V):
        return IV.schottky_richardson(V,self.Vbh,self.n,self._Is,self._KbT)
                

    @staticmethod
    def schottky_richardson(V,Vbh,n,Is,KbT):
        I=Is*np.exp(-Vbh/(KbT)+V/(n*KbT))*(1-np.exp(-V/(KbT)))
        return I

    

def r_squared(y_sampled, y_estimated):
    """Give the correlation coefficient between sampled data eand estimate data
    
    Args:
        y_sampled (np.array): data sampled
        y_estimated (np.array): data estimated by fitting
        
    Returns:
        float. squared correlation coefficient
    """
    if y_estimated==None:
        return np.NAN
    sse = sum( (y_sampled - y_estimated)**2 )
    sst = sum( (y_sampled - np.mean(y_sampled) )**2 )
    return 1 - sse / sst
