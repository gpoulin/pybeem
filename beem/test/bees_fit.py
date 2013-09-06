# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 02:11:17 2013

@author: Guillaume Poulin
"""

from beem.io import bees_from_file
from beem.experiment import BEESFit
import numpy as np

def test_fit():
    a=bees_from_file('/disk/Dropbox/nus/master/BEEM/2012-12-26/BEEM_HfO-3_D3_001.dat')
    b=BEESFit(a[0])
    b.update(b._auto_range_fit(auto_range=0.4,noise=0.1,barrier_height=[-0.8],trans_a=[0.1]))
    print(b.barrier_height[0],b.trans_a[0],b.noise,np.sqrt(b.r_squared))

    
if __name__ == "__main__":
    test_fit()
