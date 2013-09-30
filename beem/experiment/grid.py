import multiprocessing as mp
import numpy as np
from .experiment import Experiment
from .bees_fit import BEESFit
from copy import copy

class Grid(Experiment):

    def __init__(self,**kwd):
        super().__init__(**kwd)
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
        ret=copy(self)
        ret.bees+=other.bees
        ret.beesfit+=other.beesfit
        ret.src_files+=other.src_files
        
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
            ## unlink the bees to prevent to pickle to big data
            for x in self.beesfit:
                x.parent = None
                for y in x.data:
                    y.parent = None
            beesfit=p.map(fit_para,self.beesfit)
            ## relink the bees
            for x in self.beesfit:
                x.parent = self
                for y in x.data:
                    y.parent = self
            p.close()
            for i in range(len(beesfit)):
                self.beesfit[i].update(beesfit[i])
        print(time()-t1)


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
                for i in range(2,len(l)+1):
                    l[i-1].pass_number=i

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
