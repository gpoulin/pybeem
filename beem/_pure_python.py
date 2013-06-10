"""
Module that implement model function in pure python (use :mod:_pure_c module
for higher speed. 
"""

import numpy as np

def bell_kaiser_v(bias,n,params):    
    '''Function that return the BEEM current for given bias according to the
    Bell Kaiser V model with multiple barrier heights
    
    ..math:: I_{BEEM}=offset+\frac{a_1}{V}(V-\Phi_1)^n+
        \frac{a_2}{V}(V-\Phi_2)^n+\dots
    
    :param  bias: Bias to compute
    :type bias: ndarray
    :param n: parameter n of the Bell Kasier V model
    :type n: float
    :param params: parameters of the Bell Kaiser V model\
            params[0]=offset\
            params[1:x-1]=:math:`\Phi_1,\Phi_2,\dots,\Phi_{x-1}`\
            params[x:2x-1]=:math:`a_1,a_2,\dots,a_{x-1}`
    :type params: ndarray
            
    :return: BEEM current according to the model
    :rtype: ndarray
    '''    
    i_beem = np.empty(len(bias))
    i_beem[:]=params[0]
    nbh=int(len(params)-1)/2
    negative=bias[0]<0
    
    for bh, a in zip(params[1:nbh+1],params[nbh+1:2*nbh+1]):
        if negative:
            i=bias<bh
        else:
            i=bias>bh
        V=bias[i]
        i_beem[i]+=-a*np.abs((V-bh))**n/V
        
    return i_beem
    

def residu_bell_kaiser_v(params,bias,i_beem,n):
    '''Function that compute the residu of an estimation of a set of parameter
    for the Bell Kaiser V model. Useful to use with scipy.optimize.leastsq

    :param  bias: Bias to compute
    :type bias: ndarray
    :param n: parameter n of the Bell Kasier V model
    :type n: float
    :param params: parameters of the Bell Kaiser V model\
            params[0]=offset\
            params[1:x-1]=:math:`\Phi_1,\Phi_2,\dots,\Phi_{x-1}`\
            params[x:2x-1]=:math:`a_1,a_2,\dots,a_{x-1}`
    :type params: ndarray
    :param i_beem: BEEM current measured
    :rtype: ndarray
    '''
    return bell_kaiser_v(bias,n,params)-i_beem
