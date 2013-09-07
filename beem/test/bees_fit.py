# -*- coding: utf-8 -*-

from beem.io import bees_from_file
from beem.experiment import BEESFit, use_pure_c
import numpy as np

def test_fit():
    a=bees_from_file('/disk/Dropbox/nus/master/BEEM/2012-12-26/BEEM_HfO-3_D3_001.dat')
    b=BEESFit(a[0])
    c=b._auto_range_fit(auto_range=0.4,noise=0.1,barrier_height=[-0.8],trans_a=[0.1])
    use_pure_c(False)
    d=b._auto_range_fit(auto_range=0.4,noise=0.1,barrier_height=[-0.8],trans_a=[0.1])
    print(d['barrier_height'],c['barrier_height'])

    
if __name__ == "__main__":
    test_fit()
