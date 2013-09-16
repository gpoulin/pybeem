#!/usr/bin/python3
"""Module that implement all plotting with matplotlib
"""

import numpy as np
import scipy as sp
import matplotlib.pyplot as mpl

def dualplot(bees,**kwds):
    bh = np.abs([x.barrier_height[0] for x in bees])
    r = [x.trans_r[0] for x in bees]
    h = mpl.hist2d(bh, r, **kwds)
    c = mpl.colorbar()
    mpl.xlabel('$\phi$ (eV)')
    mpl.ylabel('R (eV$^{-1}$)')
    return h, c

def contourDual(bees,bins=6,range=None, bh_index=0,**kwds):
    bh=np.abs([x.barrier_height[bh_index] for x in bees])
    r=[x.trans_r[bh_index] for x in bees]
    if range!=None:
        range=[range[1],range[0]]
    H,X,Y=np.histogram2d(r,bh,bins=bins,range=range)
    extent = [Y[0], Y[-1], X[0], X[-1]]
    CS1=mpl.contourf(H,200,extent=extent,**kwds)
    c=mpl.colorbar(CS1)
    c.locator=mpl.MaxNLocator(integer=True)
    c.update_ticks()
    mpl.xlabel('$\phi$ (eV)')
    mpl.ylabel('R (eV$^{-1}$)')
    return (CS1,c)

def normplot(x,*arg,**kwarg):
    y=sp.special.erfinv(np.linspace(-1,1,len(x)+2)[1:-1:])
    sx=np.sort(x)
    mpl.plot(sx,y,*arg,**kwarg)

    p = np.array([0.001, 0.003, 0.01, 0.02, 0.05, 0.10, 0.25, 0.5, 0.75, 0.90,
                  0.95, 0.98, 0.99, 0.997, 0.999])

    label = np.array(['0.001', '0.003', '0.01','0.02','0.05','0.10','0.25',
                      '0.50', '0.75','0.90','0.95','0.98','0.99','0.997',
                      '0.999'])

    position=sp.special.erfinv(p*2-1)

    mpl.yticks(position,label)
    mpl.grid()

def cdfplot(x,*arg,**kwarg):
    y=np.linspace(0,1,len(x))
    sx=np.sort(x)
    mpl.plot(sx,y,*arg,**kwarg)

if __name__ == "__main__":
    pass
