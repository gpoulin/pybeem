# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 02:11:17 2013

@author: Guillaume Poulin
"""

from BEEM.IO import *
from BEEM.Experiment import *
import matplotlib.pyplot as plt
import os

def test_fit():
    a=BEESFromFile('/home/guillaume/Dropbox/nus/master/BEEM/2012-12-26/BEEM_HfO-3_D3_001.dat')
    #a=BEESFromFile('/home/guillaume/key/BEEM_Co-3h_A3_025.dat')
    #folder='/home/guillaume/key/Au-W/'
    #for filename in os.listdir(folder):
        #a=BEESFromFile(folder+filename)
    b=BEESFit(a[0])
    b.auto_range_fit(auto_range=0.4,noise=0.1,barrier_height=-0.8,trans_a=0.1)
        #print(b.barrier_height,b.trans_a,b.noise,np.sqrt(b.r_squared))
    b.export_plot()
    plt.show()

    
if __name__ == "__main__":
    test_fit()
