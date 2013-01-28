# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""

import numpy as np
import scipy.optimize as op
import pylab
import multiprocessing as mp
import time

_use_pureC=True

bell_kaiser_v=None
residu_bell_kaiser_v=None

def use_pureC(val=True):
    global bell_kaiser_v,residu_bell_kaiser_v,_use_pureC
    if val==True:
        try:
            bell_kaiser_v=_pureC.bell_kaiser_v
            residu_bell_kaiser_v=_pureC.residu_bell_kaiser_v
            return
        except :
            pass
        
    bell_kaiser_v=_purePython.bell_kaiser_v
    residu_bell_kaiser_v=_purePython.residu_bell_kaiser_v

import _purePython as _purePython

try:
    import _pureC as _pureC
    use_pureC(True)
except ImportError:
    use_pureC(False)
    

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
        self.noise = None
        self.n=2
        self.combine = combine_mean
        self.method = BEEM_MODEL['bkv']
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
        if self.method==BEEM_MODEL["bkv"]:
            return bell_kaiser_v(self.bias_fitted,self.n,
                        np._r[self.noise, self.barrier_height,self.trans_a]);
        
        return None
    
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
    
    def fit(self, barrier_height = [-0.8], trans_a = [0.001], noise = 1e-9):
        
        if barrier_height<self.bias_min or barrier_height>self.bias_max:
            barrier_height=(self.bias_min+self.bias_max)/2
        
        try:
            ydata=self.i_beem_fitted
            if self.method==BEEM_MODEL['bkv']:
                func=residu_bell_kaiser_v
                p0=[noise, barrier_height, trans_a]
                args=(self.bias_fitted,ydata,self.n)
            
            #Curve fit and compute error
            popt, pcov,info,mesg,ier = op.leastsq(func,p0,args,maxfev=2000,full_output=1)
            if (len(ydata) > len(p0)) and pcov is not None:
                s_sq = (func(popt, *args)**2).sum()/(len(ydata)-len(p0))
                pcov = pcov * s_sq
            else:
                pcov = np.inf
            
            
            self.barrier_height = popt[1]
            self.trans_a = popt[2]
            self.noise = popt[0]
            self.barrier_height_err=np.sqrt(pcov[1,1])
            self.trans_a_err=np.sqrt(pcov[2,2])
            self.noise_err=np.sqrt(pcov[0,0])
        except:
            self.barrier_height = None
            self.trans_a = None
            self.noise = None
            self.barrier_height_err=[np.inf]
            self.trans_a_err=[np.inf]
            self.noise_err=np.inf
            
        
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
            if threads==-1:
                p=mp.Pool()
            else:
                p=mp.Pool(threads)
            beesfit=p.map(fit_para,self.beesfit)       
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
    '''Fit BEES and return a dict of the optimal parameters. \
    Useful for multiprocessing otherwise simply x.auto_range_fit()
    
    Args:
        x (BEESFit): BEES to fit
        
    Return:
        dict. Dictionnary containing all the attributes of x that need to be\
            modifed to be fitted fitted
    '''
    x.auto_range_fit()
    return {'barrier_height':x.barrier_height,'trans_a':x.trans_a,'noise':x.noise,
        'barrier_height_err':x.barrier_height_err,'trans_a_err':x.trans_a_err,'noise_err':x.noise_err,
        'bias_max':x.bias_max,'bias_min':x.bias_min}

    

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
    
    
def combine_mean(x):
    return np.mean(x,0)
    
def BEES_position(bees_list):
    """Sort bees in a list according to their position
    
    """    

    bees_list=np.array(bees_list)
    x = np.unique(filter(None,[b.pos_x for b in bees_list]))
    y = np.unique(filter(None,[b.pos_y for b in bees_list]))
    
    #create array of empty lists
    grid=np.array([[None]*len(x)]*len(y))
    grid=np.frompyfunc(lambda x:[],1,1)(grid)
    
    for bees in bees_list:
        if not(bees.pos_x==None) and not(bees.pos_y==None):
            grid[x==bees.pos_x,y==bees.pos_y][0].append(bees)
     
    return (x,y,grid)
    
