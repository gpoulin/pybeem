import numpy as np
import scipy.optimize as op

from .experiment import BEEM_MODEL, MODE, bell_kaiser_v, residu_bell_kaiser_v
from beem.experiment.bees_data import BEESData
from .optimize import leastsq
from .experiment import r_squared

#Force error instead of warning
import warnings
warnings.simplefilter('error', RuntimeWarning)

class BEESFit(object):

    def __init__(self,data=None):
        self.data = []
        self.add_data(data)
        self.filter = None
        self.trans_a = [None]
        self.barrier_height = [None]
        self.noise = None
        self.n = 2
        self.auto_range = True
        self.range = 0.4
        self.barrier_height_init = [-0.8]
        self.trans_a_init = [0.001]
        self.noise_init = 1e-9
        self.combine = combine_mean
        self.method = BEEM_MODEL['bkv']
        self.bias_max = np.max(self.bias)
        self.bias_min = np.min(self.bias)
        self.positive = self.bias_min>0
        self.barrier_height_err = [None]
        self.trans_a_err = [None]
        self.noise_err = None
        self.id = BEESFitID()
        self.parent=None
        self._bias_max = self.bias_max
        self._bias_min = self.bias_min
        if data!=None:
            self._index = [True]*len(self.bias)

    def __eq__(self,other):
        return self.id==other.id

    def update(self,dic):
        for key in dic:
            setattr(self,key,dic[key])

    @property
    def bias(self):
        if not(self.data):
            return None
        else:
            return self.data[0].bias

    @property
    def index(self):
        if (self.bias_max!=self._bias_max or self.bias_min != self._bias_min):
          index = np.logical_and(self.bias <= self.bias_max,
                               self.bias >= self.bias_min)
          self._index = index
          self._bias_max = self.bias_max
          self._bias_min = self.bias_min
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
        if self.barrier_height[0]==None:
            return None
        if self.method==BEEM_MODEL["bkv"]:
            return bell_kaiser_v(self.bias_fitted,self.n,
                        np.r_[self.noise, self.barrier_height,self.trans_a]);
        return None


    def _wrap_bees(self,attribute):
        if not(self.data):
            return None
        att =  np.array([t.__getattribute__(attribute) for t in self.data])
        if all(att == att[0]):
            return att[0]
        else:
            return None

    @property
    def date(self):
        return self._wrap_bees('date')

    @property
    def device(self):
        return self._wrap_bees('device')

    @property
    def sample(self):
        return self._wrap_bees('sample')

    @property
    def x_index(self):
        return self._wrap_bees('x_index')

    @property
    def y_index(self):
        return self._wrap_bees('y_index')

    @property
    def pos_x(self):
        return self._wrap_bees('pos_x')
        
    @property
    def pos_y(self):
        return self._wrap_bees('pos_y')
        
    @property
    def mode(self):
        return self._wrap_bees('mode')
        
    @property
    def number(self):
        return self._wrap_bees('number')
        
    @property
    def pass_number(self):
        return self._wrap_bees('pass_number')
        
    @property
    def pos_y(self):
        return self._wrap_bees('pos_y')

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
    def pos_z(self):
        if not(self.data):
            return None

        if len(self.data)>1:
            combined=self.combine([t.pos_z for t in self.data])
        else:
            combined=self.data[0].pos_z

        if self.filter==None:
            pos_z=combined
        else:
            pos_z = self.filter(combined)
        return pos_z

    @property
    def trans_r(self):
        if self.trans_a[0]==None:
            return [None]
        return self.trans_a/np.mean(self.i_tunnel)

    @property
    def trans_r_err(self):
        if self.trans_a_err[0]==None:
            return [None]
        return self.trans_a_err/np.mean(self.i_tunnel)

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
        if bid in self.parent.beesfit_dict:
            return self.parent.beesfit_dict[bid]
        else:
            return None

    def get_previous_sweep(self):
        bid=self.id.previous_sweep()
        if bid in self.parent.beesfit_dict:
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
            self.data+=data

    def _fit(self, barrier_height = [-0.8], trans_a = [0.001], noise = 1e-9):

        try:
            b=len(barrier_height)
            ydata=self.i_beem_fitted
            if self.method==BEEM_MODEL['bkv']:
                func=residu_bell_kaiser_v
                p0=[noise]+list(barrier_height)+list(trans_a)
                args=(self.bias_fitted,ydata,self.n)


            #Curve fit and compute error
            #popt, pcov,info,mesg,ier = op.leastsq(func,p0,args,full_output=1)
            popt, pcov= leastsq(func,p0,args,full_output=1)
            if (len(ydata) > len(p0)) and pcov is not None:
                s_sq = (func(popt, *args)**2).sum()/(len(ydata)-len(p0))
                pcov = pcov * s_sq
                err=np.diag(pcov)
            else:
                pcov = np.inf
                err=[np.inf]*(1+2*b)

            return {'barrier_height':popt[1:b+1],
                    'trans_a':popt[b+1:2*b+1],
                    'noise': popt[0],
                    'barrier_height_err':np.sqrt(err[1:b+1]),
                    'trans_a_err':np.sqrt(err[b+1:2*b+1]),
                    'noise_err':np.sqrt(err[0])}
        except:
            return {'barrier_height':[None],
                    'trans_a':[None],
                    'noise':None,
                    'barrier_height_err':[np.inf],
                    'trans_a_err':[np.inf],
                    'noise_err':np.inf}

    def _auto_range_fit(self, barrier_height = [-0.8], trans_a = [0.001],
                       noise = 1e-9, auto_range = 0.4, tol = 0.001,
                       maxIt=10, conv_ratio=1):

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
            if b['barrier_height']==a['barrier_height']:
              b=self._fit(a['barrier_height']*1.1,a['trans_a']*0.1, a['noise'])

            if b['barrier_height'][0]!=None and\
                    np.abs(b['barrier_height'][0]-a['barrier_height'][0])<tol:
                b.update({'bias_max':self.bias_max,'bias_min':self.bias_min})
                return b

            #if barrier not found look further
            if b['barrier_height'][0]==None or\
                    np.abs(b['barrier_height_err'][0]/b['barrier_height'][0])\
                    >0.04:
                if self.bias_max<0:
                    self.bias_min=max(self.bias_min-auto_range,lim)
                else:
                    self.bias_max=min(self.bias_max+auto_range,lim)
            else:
                if b['barrier_height'][0]>self.bias_max or\
                        b['barrier_height'][0]<self.bias_min:
                    b['barrier_height'][0]=(self.bias_max+self.bias_min)/2
                elif self.bias_max<0:
                    self.bias_min=conv_ratio*b['barrier_height'][0]+\
                            conv_inv*a['barrier_height'][0]-auto_range
                else:
                    self.bias_max=conv_ratio*b['barrier_height'][0]+\
                            conv_inv*a['barrier_height'][0]+auto_range
                a=b

        if(b['barrier_height'][0]==None or\
                np.abs(b['barrier_height_err'][0]/b['barrier_height'][0])>0.1):

            b={'barrier_height':[None],
               'trans_a':[None],
               'noise':None,
               'barrier_height_err':[np.inf],
               'trans_a_err':[np.inf],
               'noise_err':np.inf}

        b.update({'bias_max':self.bias_max,'bias_min':self.bias_min})
        return b

    def fit(self,auto=None,**kwarg):
        if auto==None and self.auto_range:
            return self._auto_range_fit(auto_range=self.range,**kwarg)
        elif auto==None:
            return self._fit(**kwarg)
        elif auto:
            return self._auto_range_fit(auto_range=self.range,**kwarg)
        else:
            return self._fit(**kwarg)

    def fit_update(self,**kwarg):
        self.update(self.fit(**kwarg))

    @property
    def r_squared(self):
        if self.barrier_height[0]==None:
            return np.nan
        return r_squared(self.i_beem_fitted,self.i_beem_estimated)




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
        return int(h*100+10*self.n)


    def __eq__(self,other):
        if len(self.bees)!=len(other.bees):
            return False
        self.bees.sort()
        other.bees.sort()

        for x in range(len(self.bees)):
            if self.bees[x]!=other.bees[x]:
                return False
        return self.n==other.n

    def __ne__(self,other):
        return not(self==other)

    def __str__(self):
        s=''
        self.bees.sort()
        for k in self.bees:
            s+=str(k)+'__'

        s+='%2.2f'%self.n
        return s

def combine_mean(x):
    return np.mean(x,0)
