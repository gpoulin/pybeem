# -*- coding: utf-8 -*-
"""
Created on Sun Jan 20 21:44:13 2013

@author: Guillaume Poulin
"""

cimport numpy as np
from numpy import empty

def bell_kaiser_v(np.ndarray[double, ndim=1] bias, double barrier_height, double trans_a, double noise):
    
    cdef unsigned int l= len(bias)
    cdef unsigned int i=0
    cdef double bi
    cdef np.ndarray[double, ndim=1] i_beem = empty(dtype='float', shape=(l,))
    cdef double k    
    
    for i in range(l):
        bi=bias[i]

        if bi>barrier_height:
            i_beem[i]=noise
        else:
            k=bi-barrier_height
            i_beem[i]=-trans_a*k*k/bi+noise
    return i_beem
