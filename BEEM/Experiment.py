# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""
import _pureC
#import cfunction
import numpy as np
import scipy.optimize as op
import pylab
import multiprocessing as mp
import time
#from scipy import weave


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
        self.trans_a = None
        self.barrier_height = None
        self.barrier_height_max=-0.5
        self.noise = None
        self.combine = combine_mean
        self.method = _pureC.bell_kaiser_v
        self.bias_max=np.max(self.bias)
        self.bias_min=np.min(self.bias)
        self.positive=self.bias_min>0
        self.updated = False
        self.barrier_height_err=None
        self.trans_a_err=None
        self.noise_err=None
        
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
            return combined
        else:
            return self.filter(combined)
        
    @property
    def i_tunnel(self):
        if not(self.data):
            return None
        
        if len(self.data)>1:
            combined=self.combine([t.i_tunnel for t in self.data])
        else:
            combined=self.data[0].i_tunnel
        
        if self.filter==None:
            i_tunnel=combined
        else:
            i_tunnel = self.filter(combined)
        return i_tunnel
    
    @property
    def trans_r(self):
        return self.trans_a/np.mean(self.i_tunnel)
    
    def reset(self):
        self.barrier_height = None
        self.trans_a = None
        self.noise = None
        self.updated = False
    
    def add_data(self, data):
        self.reset()
        if isinstance(data,BEESData):
            self.data.append(data)
        else:
            for bees in data:
                 self.data.append(bees)
    
    def fit(self, barrier_height = -0.8, trans_a = 0.001, noise = 1e-9):
        
        if barrier_height<self.bias_min or barrier_height>self.bias_max:
            barrier_height=(self.bias_min+self.bias_max)/2
        
        try:
            popt, pconv = op.curve_fit(self.method, self.bias_fitted, self.i_beem_fitted,
                                   [barrier_height, trans_a, noise],maxfev=2000)
            
            self.barrier_height = popt[0]
            self.trans_a = popt[1]
            self.noise = popt[2]
            self.barrier_height_err=np.sqrt(pconv[0,0])
            self.trans_a_err=np.sqrt(pconv[1,1])
            self.noise_err=np.sqrt(pconv[2,2])
        except:
            self.barrier_height = None
            self.trans_a = None
            self.noise = None
            #self.barrier_height_err=np.inf
            #self.trans_a_err=np.inf
            #self.noise_err=np.inf
            
        
    def export_plot(self,fig=1):
        fig=pylab.figure(fig,figsize=(6,6),dpi=120)
        pylab.rc('text', usetex=True)
        p1,=pylab.plot(self.bias, self.i_beem/np.mean(self.i_tunnel),'ow')
        pylab.hold(True)
        p2,=pylab.plot(self.bias_fitted,self.i_beem_estimated/np.mean(self.i_tunnel),'r',linewidth=2)       
        pylab.xlabel('Bias (V)')
        pylab.ylabel(r'BEEM Current, $\frac{I_b}{I_T}$')
        power=int(np.floor(np.log10(self.trans_r)))
        val=self.trans_r/10**power
        ypos=np.mean(pylab.ylim())
        _,xpos=pylab.xlim()
        t=pylab.text(xpos,ypos,
                        r'\begin{tabular}{rcl} Barrier Height:&$%0.3f$&eV\\R:&$%0.3f\times10^{%d}$&eV$^{-1}$\end{tabular}'%(np.abs(self.barrier_height),val,power),
                        horizontalalignment='right',verticalalignment='center')
        pylab.legend(['BEES data','Fitted data'],loc=1,numpoints=1)        
        return fig,t
    
    def auto_range_fit(self, barrier_height = -0.8, trans_a = 0.001, 
                       noise = 1e-9, auto_range = 0.4, tol = 0.001):
        self.barrier_height = barrier_height
        self.trans_a = trans_a
        self.noise = noise
        
        
        if barrier_height<0:
            self.bias_min=barrier_height-auto_range
        else:
            self.bias_max=barrier_height+auto_range
        
        if self.bias_max<0:
            lim=min(self.bias)
        else:
            lim=max(self.bias)
            
        
        for i in range(0,10):
            self.fit(self.barrier_height, self.trans_a, self.noise)
            
            #if barrier not found look further
            if self.barrier_height==None or np.abs(self.barrier_height_err/self.barrier_height)>0.04:
                self.barrier_height = barrier_height
                self.trans_a = trans_a
                self.noise = noise
                if self.bias_max<0:
                    self.bias_min=max(self.bias_min-auto_range,lim)
                else:
                    self.bias_max=min(self.bias_max+auto_range,lim)
            else:
                if np.abs(barrier_height-self.barrier_height)<tol:
                    return
                if self.barrier_height>self.bias_max or self.barrier_height<self.bias_min:
                    self.barrier_height=(self.bias_max+self.bias_min)/2
                if self.barrier_height<0:
                    self.bias_min=(2*self.barrier_height+barrier_height)/3-auto_range
                else:
                    self.bias_max=(2*self.barrier_height+barrier_height)/3+auto_range
                barrier_height=self.barrier_height
            
        
    @property
    def r_squared(self):
      return r_squared(self.i_beem_fitted,self.i_beem_estimated)
        
    

    
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
                    
    def fit(self,threads=1):
        
        t1=time.time()
        if threads==1:     
            for x in self.beesfit:
                x.auto_range_fit()
        else:
            p=mp.Pool(threads)
            beesfit=p.map(fit_para,self.beesfit)
            p.close()            
            for i in range(0,len(beesfit)):
                for x in beesfit[i].keys():
                    self.beesfit[i].__setattr__(x,beesfit[i][x])
        t2=time.time()
        print t2-t1
        
        
                
            
    def extract_good(self,r_squared=0.6):
        fit=np.array(self.beesfit)
        r=np.array([x.r_squared for x in fit])
        return fit[np.logical_and(r>r_squared,r<1)]
        

def fit_para(x):
    x.auto_range_fit()
    return {'barrier_height':x.barrier_height,'trans_a':x.trans_a,'noise':x.noise,
        'barrier_height_err':x.barrier_height_err,'trans_a_err':x.trans_a_err,'noise_err':x.noise_err,
        'bias_max':x.bias_max,'bias_min':x.bias_min}

    

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



def bell_kaiser_v(bias, barrier_height, trans_a, noise):    
    i_beem = np.zeros(bias.shape[0])
    x=np.abs(bias) > np.abs(barrier_height)
    bias=bias[x]
    k=bias-barrier_height
    i_beem[x] = -trans_a*k*k / bias
    return i_beem + noise

def bell_kaiser(bias, barrier_height, trans_a, noise):
    i_beem = np.ones(bias.shape[0]) * noise
    i_beem[bias < barrier_height] = (-trans_a * 
        (bias[bias < barrier_height] - barrier_height)**2 ) + noise
    return i_beem
    
def combine_mean(x):
    return np.mean(x,0)