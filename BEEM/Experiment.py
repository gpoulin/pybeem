# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""

import numpy as np
import scipy.optimize as op
import multiprocessing as mp
import scipy.constants as constants


#Force error instead of warning
import warnings
warnings.simplefilter('error',RuntimeWarning)

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
        self.pass_number=-1
        self.x_index=-1
        self.y_index=-1
        self.id=BEESID()
        self.parent=None
    
    def __cmp__(self,other):
        return self.id.__cmp__(other.id)
        

    def set_id(self):
        self.id.x_index=self.x_index
        self.id.y_index=self.y_index
        self.id.mode=self.mode
        self.id.number=self.number
        self.id.pass_number=self.pass_number
        
class BEESFit(object):
    
    def __init__(self,data=None):
        self.data = []
        self.add_data(data)
        self.filter = None
        self.trans_a = [None]
        self.barrier_height = [None]
        self.noise = None
        self.n=2
        self.auto_range=True
        self.range=0.4
        self.barrier_height_init=[-0.8]
        self.trans_a_init=[0.001]
        self.noise_init=1e-9
        self.combine = np.mean(x,0)
        self.method = BEEM_MODEL['bkv']
        self.bias_max=np.max(self.bias)
        self.bias_min=np.min(self.bias)
        self.positive=self.bias_min>0
        self.barrier_height_err=[None]
        self.trans_a_err=[None]
        self.noise_err=None
        self.id=BEESFitID()
        self.parent=None
        self._bias_max=self.bias_max
        self._bias_min=self.bias_min
        if data!=None:
          self._index=[True]*len(self.bias)
        
    def __cmp__(self,other):
        return self.id.__cmp__(other.id)
        
    @property
    def bias(self):
        if not(self.data):
            return None
        else:
            return self.data[0].bias
    
    @property
    def index(self):
        if (self.bias_max!=self._bias_max or self.bias_min!=self._bias_min):
          index=np.logical_and(self.bias <= self.bias_max, 
                               self.bias >= self.bias_min)
          self.index=index
          self._bias_max=self.bias_max
          self._bias_min=self.bias_min
        return self._index
    
    @property
    def i_beem_fitted(self):
        return self.i_beem[self.index]

    @property
    def i_tunnel_fitted(self):
        return self.i_tunnel[self.index]
        
    @property
    def bias_fitted(self):
        return self.bias[self.index]
        
    @property
    def i_beem_estimated(self):
        if self.barrier_height==None:
            return None
        if self.method==BEEM_MODEL["bkv"]:
            return bell_kaiser_v(self.bias_fitted,self.n,
                        np.r_[self.noise, self.barrier_height,self.trans_a]);
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
        
    def set_id(self):
        self.id=BEESFitID()
        for b in self.data:
            self.id.bees.append(b.id)
        
        self.id.n=self.n
        
    def get_reverse_mode(self):
        bid=self.id.switch_mode()
        return self.parent.beesfit_dict[bid]
        
    def get_next_sweep(self):
        bid=self.id.next_sweep()
        if self.parent.beesfit_dict.has_key(bid):
            return self.parent.beesfit_dict[bid]
        else:
            return None
        
    def get_previous_sweep(self):
        bid=self.id.previous_sweep()
        if self.parent.beesfit_dict.has_key(bid):
            return self.parent.beesfit_dict[bid]
        else:
            return None
            
            
    def get_same_pos(self,sweep,mode,pass_number=None):
        if pass_number==None:
            pass_number=self.data[0].pass_number
        
        k=self.id.copy()
        for b in k.bees:
            b.pass_number=pass_number
            b.number=sweep
            b.mode=mode
        
        return self.parent.beesfit_dict[k]
    
    def add_data(self, data):
        if isinstance(data,BEESData):
            self.data.append(data)
        else:
            self.data+=bees

    def set_fitting(self,param):
        self.update(param)
    
    def _fit(self, barrier_height = [-0.8], trans_a = [0.001], noise = 1e-9):

        try:
            b=len(barrier_height)
            ydata=self.i_beem_fitted
            if self.method==BEEM_MODEL['bkv']:
                func=residu_bell_kaiser_v
                p0=np.r_[noise,barrier_height,trans_a]
                args=(self.bias_fitted,ydata,self.n)
            
            #Curve fit and compute error
            popt, pcov,info,mesg,ier = op.leastsq(func,p0,args,maxfev=2000,full_output=1)
            if (len(ydata) > len(p0)) and pcov is not None:
                s_sq = (func(popt, *args)**2).sum()/(len(ydata)-len(p0))
                pcov = pcov * s_sq
            else:
                pcov = np.inf
            
            err=np.diag(pcov)
            return {'barrier_height':popt[1:b+1], 'trans_a':popt[b+1:2*b+1],'noise': popt[0], 
                'barrier_height_err':np.sqrt(err[1:b+1]),'trans_a_err':np.sqrt(err[b+1:2*b+1])
                'noise_err':np.sqrt(err[0])}
        except:
          return {'barrier_height':[None],'trans_a':[None],'noise':None,
              'barrier_height_err':[np.inf],'trans_a_err':[np.inf],'noise_err':np.inf}
        
    def _auto_range_fit(self, barrier_height = [-0.8], trans_a = [0.001], 
                       noise = 1e-9, auto_range = 0.4, tol = 0.001, maxIt=10, conv_ratio=2/3):

        conv_inv=1-conv_ratio
        
        a={'barrier_height':barrier_height,'trans_a':trans_a,'noise':noise}
                
        if barrier_height[0]<0:
            self.bias_min=barrier_height[0]-auto_range
        else:
            self.bias_max=barrier_height[0]+auto_range
        
        if self.bias_max<0:
            lim=min(self.bias)
        else:
            lim=max(self.bias)
            
        
        for i in range(maxIt):
            b=self._fit(a['barrier_height'],a['trans_a'], a['noise'])

            if np.abs(b['barrier_height'][0]-a['barrier_height'][0])<tol:
              break
            
            #if barrier not found look further
            if b['barrier_height'][0]==None or b['barrier_height'][0]>self.bias_max or b['barrier_height'][0]<self.bias_min or np.abs(b['barrier_height_err'][0]/b['self.barrier_height'][0])>0.04:
                if self.bias_max<0:
                    self.bias_min=max(self.bias_min-auto_range,lim)
                else:
                    self.bias_max=min(self.bias_max+auto_range,lim)
            else:
                if self.bias_max<0:
                    self.bias_min=conv_ratio*b['barrier_height'][0]+conv_inv*a['barrier_height'][0]-auto_range
                else:
                    self.bias_max=conv_ratio*b['barrier_height'][0]+conv_inv*a['barrier_height'][0]+auto_range
                a=b

        return b
  
    def fit():
        _fit()

    def fit_update(self,*arg,**kwarg):
        self.update(self.fit(*arg,**kwarg))
        
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
            beesfit=p.map(lamda x:x.fit(),self.beesfit)
            p.close()
            for i in range(len(beesfit)):
                self.beesfit[i].update(beesfit[i])
        t2=time()
        print(t2-t1)
        
    def set_coord(self):
        self.xs = np.unique(filter(lambda x: not(x==None),[b.pos_x for b in self.bees]))
        self.ys = np.unique(filter(lambda x: not(x==None),[b.pos_y for b in self.bees]))
    
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
            if dic.has_key(b.id):
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
        self.KbT=constants.physical_constants['Boltzmann constant in eV/K'][0]*self.T
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
        popt,pconv=op.curve_fit(self._model_fit,self.V_fitted,np.log(np.abs(self.I_fitted)),[Vbh_init,n_init])
        self.barrier_height=popt[0]
        self.n=popt[1]
        self.r_squared=r_squared(np.log(np.abs(self.I_fitted)),self._model_fit(self.V_fitted,popt[0],popt[1]))


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
    
class BEESID(object):
    
    def __init__(self):
        self.x_index=0
        self.y_index=0
        self.pass_number=0
        self.number=0
        self.mode=MODE['fwd']
    
    def __hash__(self):
        return self.mode+10*self.number+1000*self.pass_number+100000*self.y_index+100000000*self.x_index
    
    def __cmp__(self,other):
        l=['x_index','y_index','pass_number','number','mode']
        for x in l:
            a=int.__cmp__(self.__getattribute__(x),other.__getattribute__(x))
            if not(a==0):
                return a
            
        return 0
            
    def copy(self):
        k=BEESID()
        k.x_index=self.x_index
        k.y_index=self.y_index
        k.pass_number=self.pass_number
        k.number=self.number
        k.mode=self.mode
        return k
    
    def switch_mode(self):
        k=self.copy()
        
        if k.mode==MODE['fwd']:
            k.mode=MODE['bwd']
        elif k.mode==MODE['bwd']:
            k.mode=MODE['fwd']
        
        return k
        
    def next_sweep(self):
        k=self.copy()
        k.number+=1
        return k
    
    def previous_sweep(self):
        k=self.copy()
        k.number-=1
        return k
        
            
    def __str__(self):
        return '%03d_%03d_%03d_%03d_%02d'%(self.x_index,self.y_index,self.pass_number,self.number,self.mode)
            
        

class BEESFitID(object):
    
    def __init__(self):
        self.bees=[]
        self.n=0
        
    def copy(self):
        b=BEESFitID()
        b.bees=self.bees[:]
        b.n=self.n
        return b
        
    def switch_mode(self):
        b=self.copy()
        for bt in range(len(b.bees)):
            b.bees[bt]=b.bees[bt].switch_mode()
        return b
    
    def next_sweep(self):
        b=self.copy()
        for bt in range(len(b.bees)):
            b.bees[bt]=b.bees[bt].next_sweep()
        return b

    def previous_sweep(self):
        b=self.copy()
        for bt in range(len(b.bees)):
            b.bees[bt]=b.bees[bt].previous_sweep()
        return b
    
    
    def __hash__(self):
        h=0
        self.bees.sort()
        for x in self.bees:
            h+=x.__hash__()
        return h*100+int(10*self.n)
        
    
    def __cmp__(self,other):
        a=int.__cmp__(len(self.bees),len(other.bees))
        if not(a==0):
            return a
        self.bees.sort()
        other.bees.sort()
        
        for x in range(len(self.bees)):
            a=self.bees[x].__cmp__(other.bees[x])
            if not(a==0):
                return a
        
        return int(np.sign(self.n-other.n))
        
    def __str__(self):
        s=''
        self.bees.sort()
        for k in self.bees:
            s+=str(k)+'__'
        
        s+='%2.2f'%self.n
        return s
