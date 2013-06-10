"""
Created on Sat Dec  8 15:19:09 2012

@author: Guillaume Poulin
"""

import pylab
import numpy as np
import scipy as sp

def normplot(x,*arg,**kwarg):
    y=sp.special.erfinv(np.linspace(-1,1,len(x)+2)[1:-1:])
    sx=np.sort(x)
    pylab.plot(sx,y,*arg,**kwarg)

    p = np.array([0.001, 0.003, 0.01, 0.02, 0.05, 0.10, 0.25, 0.5, 0.75, 0.90,
                  0.95, 0.98, 0.99, 0.997, 0.999])

    label = np.array(['0.001', '0.003', '0.01','0.02','0.05','0.10','0.25',
                      '0.50', '0.75','0.90','0.95','0.98','0.99','0.997',
                      '0.999'])

    position=sp.special.erfinv(p*2-1)

    pylab.yticks(position,label)
    pylab.grid()

def cdfplot(x,*arg,**kwarg):
    y=np.linspace(0,1,len(x))
    sx=np.sort(x)
    pylab.plot(sx,y,*arg,**kwarg)

if __name__ == "__main__":
    pass
