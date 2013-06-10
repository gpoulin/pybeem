#!/usr/bin/python3
"""Module that implement all the user interface related functions and classes.
"""

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
from PyQt4 import QtGui, QtCore
 
import pyqtgraph as pg
import numpy as np
from .io import grid_from_3ds
import os
import json
import matplotlib.pyplot as mpl

signal = QtCore.pyqtSignal
slot = QtCore.pyqtSlot
property = QtCore.pyqtProperty

_pref = dict()

class BEESFitGraph(pg.PlotWidget):

    def __init__(self,parent=None):
        super().__init__(parent)
        plot = self.getPlotItem()
        self.label = pg.TextItem(anchor=(1, 0))
        plot.setLabel('left', 'BEEM Current','A')
        plot.setLabel('bottom', 'Bias','V')
        self.region = pg.LinearRegionItem([0, 1])
        self.region.sigRegionChanged.connect(self.fit)
        plot.sigRangeChanged.connect(self._update_pos)
        plot.addItem(self.region)
        plot.addItem(self.label)
        self.cara = plot.plot([np.nan], [np.nan])
        self.fitted = plot.plot([np.nan], [np.nan], pen='r')
        self.beesfit = None

    def _update_pos(self):
        plot = self.getPlotItem()
        geo = plot.viewRange()
        x = geo[0][1]
        y = geo[1][1]
        self.label.setPos(x, y)

    def _update_beem(self):
        self.cara.setData(self.beesfit.bias, self.beesfit.i_beem)

    def _update_fitted(self):
        if self.beesfit.i_beem_estimated==None:
            self.fitted.setData([np.nan], [np.nan])
        else:
            self.fitted.setData(self.beesfit.bias_fitted,
                self.beesfit.i_beem_estimated)

    def fit(self):
        vmin, vmax = self.region.getRegion()
        b=self.beesfit
        b.bias_max = vmax
        b.bias_min = vmin
        if b.r_squared>0.1:
            b.fit_update(auto=False,barrier_height=b.barrier_height,
                    trans_a=b.trans_a, noise=b.noise)
        else:
            b.fit_update(auto=False)
        self._update_fitted()


    def set_bees(self, beesfit):
        self.beesfit = beesfit
        self.region.setRegion([beesfit.bias_min, beesfit.bias_max])
        self._update_beem()
        self._update_fitted()
        self.getPlotItem().autoRange()


class BEESSelector(QtGui.QDialog):
    def __init__(self,bees_list,parent=None):
        super().__init__(parent)
        self.beesList=bees_list
        self.index=0
        self.selected=[True]*len(bees_list)
        self.fitter=BEESFitGraph()
        self.label=QtGui.QLabel()
        self.ne=QtGui.QPushButton("Next")
        self.pr=QtGui.QPushButton("Previous")
        self.check=QtGui.QCheckBox("Selected")

        hbox=QtGui.QHBoxLayout()
        hbox.addWidget(self.pr)
        hbox.addStretch(1)
        hbox.addWidget(self.check)
        hbox.addStretch(1)
        hbox.addWidget(self.ne)

        vbox=QtGui.QVBoxLayout()
        vbox.addWidget(self.fitter)
        vbox.addWidget(self.label)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.ne.clicked.connect(self.go_next)
        self.pr.clicked.connect(self.go_prev)
        self,check.stateChanged.connect(self.on_change)
        self._update()
    
    def on_change(self,a):
        if a>0:
            self.selected[self.index]=True
        else:
            self.selected[self.index]=False

    def _update(self):
        self.fitter.set_bees(self.bees_list[self.index])
        self.pr.setEnabled(True)
        self.ne.setText("Next")
        if self.index==0:
            self.pr.setEnabled(False)
        elif self.index==len(self.beesList)-1:
            self.ne.setText("Finish")
        if self.selected[self.index]:
            self.check.setChecked(True)
        else:
            self.check.setChecked(False)
        self.label.setText(str(self.index+1)+"/"+str(len(self.bees_list)))

    def go_next(self):
        if self.index==len(self.bees_list)-1:
            self.done(1)
        else:
            self.index+=1
        self._update()
    
    def go_prev(self):
        self.index-=1
        self._update()


def select_bees(bees_list):
    a=BEESSelector(bees_list)
    a.exec_()
    bees_list=np.array(bees_list)
    return bees_list[np.array(a.selected)]

def select_file(folder = None, filter = None, selected_filter = None):
    filename = QtGui.QFileDialog.getOpenFileName(directory = folder, 
                        filter = filter, selectedFilter = selected_filter)
    return filename

def open3ds(filename = None, folder = None):
    if filename == None:
        filename = select_file(folder=folder, filter=u'3ds (*.3ds)')
    return grid_from_3ds(filename)
    
def find_config():
    if os.name == 'posix':
        folder = os.path.expanduser('~/.pybeem')
    elif os.name == 'nt':
        folder = os.path.expandvars('%APPDATA%/pybeem')
    else:
        raise Exception("Don't know where to save config. OS unknown")
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + '/pybeem.conf'

def save_pref(filename = None):
    if filename == None:
        filename = find_config()
    fid = open(filename,'w')
    json.dump(_pref,fid)
    fid.close()

def load_pref(filename = None):
    global _pref
    if filename == None:
        filename = find_config()
    if os.path.exists(filename):
        fid = open(filename,'r')
        _pref.update(json.load(fid))
        fid.close()

def fit_file(filename = None, folder = None):
    if folder == None:
        folder = _pref['work_folder']
    g = open3ds(filename, folder)
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
    
def contourDual(bees,N=None,bins=None,range=None,**kwds):
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
    
    
if __name__ == "__main__":
    load_pref()
    print(_pref)
