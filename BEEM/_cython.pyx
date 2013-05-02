# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 10:41:45 2013

@author: Guillaume Poulin
"""

# cython: profile=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

cimport numpy as np
import numpy as np
cimport cython

cpdef np.ndarray[np.double_t, ndim=1] bell_kaiser_v(np.ndarray[np.double_t, ndim=1] bias,double n,np.ndarray[np.double_t, ndim=1] params):    
    '''Function that return the BEEM current for given bias according to the
    Bell Kaiser V model with multiple barrier heights
    
    ..math:: I_{BEEM}=offset+\frac{a_1}{V}(V-\Phi_1)^n+\frac{a_2}{V}(V-\Phi_2)^n+\dots
    
    Args:
        bias (ndarray): Bias to compute (V)
        n (float): n parameter
        params (ndarray): parameters of the Bell Kaiser V model \
            params[0]=offset\
            params[1:x-1]=:math:`\Phi_1,\Phi_2,\dots,\Phi_{x-1}`
            params[x:2x-1]=:math:`a_1,a_2,\dots,a_{x-1}`
            
    Return:
        ndarray
    '''
    cdef int i, j, nbh
    cdef double k
    cdef np.ndarray[np.double_t, ndim=1] i_beem
    i_beem = np.empty(bias.shape[0],np.double)
    
    nbh=(params.shape[0]-1)/2

    for j in xrange(0,bias.shape[0]):
        i_beem[j]=params[0]
        for i in xrange(0,nbh):
            k=bias[j]-params[1+i]
            i_beem[j]-=params[nbh+1+i]*k**n/bias[j]
        
    return i_beem
    

cpdef np.ndarray[np.double_t, ndim=1] residu_bell_kaiser_v(np.ndarray[np.double_t, ndim=1] params,np.ndarray[np.double_t, ndim=1] bias, np.ndarray[np.double_t, ndim=1] i_beem, double n):
    cdef np.ndarray[np.double_t, ndim=1] beemt
    cdef int i
    beemt= bell_kaiser_v(bias,n,params)
    for i in xrange(0,beemt.shape[0]):
        beemt[i]-=i_beem[i]
    return beemt
