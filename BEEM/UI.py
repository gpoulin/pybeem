#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 14:00:12 2012

@author: Guillaume Poulin
"""




import pyqtgraph as pg
import numpy as np
from IO import grid_from_3ds
import os
import json
import matplotlib.pyplot as mpl

PYSIDE = True

try:
    from PySide import QtGui, QtCore
except ImportError:
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    from PyQt4 import QtGui, QtCore
    PYSIDE = False
    
if PYSIDE:
    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
else:
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty

PREF = dict() #{
#    u'work_folder':os.path.expanduser(u'~')
#    }

class BEESFit_graph(pg.PlotWidget):

    def __init__(self,parent=None):
        super(BEESFit_graph,self).__init__(parent)
        ploti = self.getPlotItem()
        self.label = pg.TextItem(anchor=(1, 0))
        ploti.setLabel('left', u'BEEM Current','A')
        ploti.setLabel('bottom', u'Bias','V')
        self.region = pg.LinearRegionItem([0, 1])
        self.region.sigRegionChanged.connect(self.fit)
        ploti.sigRangeChanged.connect(self._updatePos)
        ploti.addItem(self.region)
        ploti.addItem(self.label)
        self.cara = ploti.plot([np.nan], [np.nan])
        self.fitted = ploti.plot([np.nan], [np.nan], pen='r')
        self.show()
        self.beesfit = None

    def _updatePos(self):
        ploti = self.getPlotItem()
        geo = ploti.viewRange()
        x = geo[0][1]
        y = geo[1][1]
        self.label.setPos(x, y)

    def _updateBEEM(self):
        self.cara.setData(self.beesfit.bias, self.beesfit.i_beem)

    def _updateFitted(self):
        try:
            r = np.sqrt(self.beesfit.r_squared)
            if np.isnan(r):
                r=0
            if not(self.beesfit.barrier_height==None):
                self.label.setText(u"Vbh=%0.5f, R=%0.5f" %\
                        (self.beesfit.barrier_height,r))

            if self.beesfit.i_beem_estimated==None:
                self.fitted.setData([np.nan], [np.nan])
            else:
                self.fitted.setData(self.beesfit.bias_fitted,
                                    self.beesfit.i_beem_estimated)
        
            self.getPlotItem().autoRange()

        except:
            pass

    def fit(self):
        Vmin, Vmax = self.region.getRegion()
        b=self.beesfit
        b.bias_max = Vmax
        b.bias_min = Vmin
        if b.r_squared>0.1:
            b.fit(b.barrier_height, b.trans_a, b.noise)
        else:
            b.fit()
        self._updateFitted()


    def set_bees(self, beesfit):
        self.beesfit = beesfit
        self.region.setRegion([beesfit.bias_min, beesfit.bias_max])
        self._updateBEEM()
        self._updateFitted()
        self.getPlotItem().autoRange()

def select_bees(bees_fit_list):
    ui = BEESFit_graph()
    selected = []
    i = 0
    j=0
    for bees in bees_fit_list:
        ui.set_bees(bees)
        x = raw_input("%d/%d:"%(i,j))
        if x == '':
            i += 1
            selected.append(bees)
        j+=1
    return selected

def select_file(folder = None, filter = None, selected_filter = None):
    if PYSIDE:
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            dir = folder, filter = filter, selectedFilter = selected_filter)
    else:
        filename = QtGui.QFileDialog.getOpenFileName(directory = folder, 
                        filter = filter, selectedFilter = selected_filter)
    return filename

def open_3ds(filename = None, folder = None):
    if filename == None:
        filename = select_file(folder=folder, filter=u'3ds (*.3ds)')
    return grid_from_3ds(filename)
    
def find_config():
    if os.name == 'posix':
        folder = os.path.expanduser(u'~/.pybeem')
    elif os.name == 'nt':
        folder = os.path.expandvars(u'%APPDATA%/pybeem')
    else:
        raise Exception(u"Don't know where to save config. OS unknown")
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + u'/pybeem.conf'

def save_pref(filename = None):
    if filename == None:
        filename = find_config()
    fid = open(filename,'w')
    json.dump(PREF,fid)
    fid.close()

def load_pref(filename = None):
    global PREF
    if filename == None:
        filename = find_config()
    if os.path.exists(filename):
        fid = open(filename,'r')
        PREF.update(json.load(fid))
        fid.close()

def fit_file(filename = None, folder = None):
    if folder == None:
        folder = PREF[u'work_folder']
    g = open_3ds(filename, folder)
    g.normal_fit()
    g.fit(-1)
    return g
    
def dualplot(bees,**kwds):
    bh=np.abs([x.barrier_height for x in bees])
    r=[x.trans_r for x in bees]
    h=mpl.hist2d(bh,r,**kwds)
    c=mpl.colorbar()
    mpl.xlabel('$\phi$ (eV)')
    mpl.ylabel('R (eV$^{-1}$)')
    return h,c
    
def contour_dual(bees,N=None,bins=None,range=None,**kwds):
    bh=np.abs([x.barrier_height for x in bees])
    r=[x.trans_r for x in bees]
    H,X,Y=np.histogram2d(r,bh,bins=bins,range=[range[1],range[0]])
    extent = [Y[0], Y[-1], X[0], X[-1]]
    if N==None:
        N=int(H.max())-1
    CS1=mpl.contourf(H,N,extent=extent,extend='min',**kwds)
    c=mpl.colorbar()
    CS2=mpl.contour(H,levels=CS1.levels,extent=extent,extend='min',colors='k')
    c.add_lines(CS2)
    mpl.xlabel('$\phi$ (eV)')
    mpl.ylabel('R (eV$^{-1}$)')
    return (CS1,c)
    
def mod():
    global PREF
    PREF['a']=2
    
if __name__ == "__main__":
    load_pref()
    print PREF