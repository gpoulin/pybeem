#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 14:00:12 2012

@author: Guillaume Poulin
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
from .IO import grid_from_3ds
import os
import json
import matplotlib.pyplot as mpl

Signal = QtCore.pyqtSignal
Slot = QtCore.pyqtSlot
Property = QtCore.pyqtProperty
#app=QtGui.QApplication([])

PREF = dict()

class BeesFitGraph(pg.PlotWidget):

    def __init__(self,parent=None):
        super().__init__(parent)
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
        self.beesfit = None

    def _updatePos(self):
        ploti = self.getPlotItem()
        geo = ploti.viewRange()
        x = geo[0][1]
        y = geo[1][1]
        self.label.setPos(x, y)

    def _updateBeem(self):
        self.cara.setData(self.beesfit.bias, self.beesfit.i_beem)

    def _updateFitted(self):
        try:
            if self.beesfit.i_beem_estimated==None:
                self.fitted.setData([np.nan], [np.nan])
            else:
                self.fitted.setData(self.beesfit.bias_fitted,
                                    self.beesfit.i_beem_estimated)

            r = np.sqrt(self.beesfit.r_squared)
            if np.isnan(r):
                r=0
            if not(self.beesfit.barrier_height[0]==None):
                self.label.setText(u"Vbh=%0.5f, R=%0.5f" %\
                        (self.beesfit.barrier_height[0],r))
        
            self.getPlotItem().autoRange()

        except:
            pass

    def fit(self):
        Vmin, Vmax = self.region.getRegion()
        b=self.beesfit
        b.bias_max = Vmax
        b.bias_min = Vmin
        if b.r_squared>0.1:
            b.fit_update(auto=False,barrier_height=b.barrier_height, trans_a=b.trans_a, noise=b.noise)
        else:
            b.fit_update(auto=False)
        self._updateFitted()


    def setBees(self, beesfit):
        self.beesfit = beesfit
        self.region.setRegion([beesfit.bias_min, beesfit.bias_max])
        self._updateBeem()
        self._updateFitted()
        self.getPlotItem().autoRange()


class BeesSelector(QtGui.QDialog):
    def __init__(self,beesList,parent=None):
        super().__init__(parent)
        self.beesList=beesList
        self.index=0
        self.selected=[True]*len(beesList)
        self.fitter=BeesFitGraph()
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
        self.connect(self.ne,QtCore.SIGNAL('clicked()'),self.goNext)
        self.connect(self.pr,QtCore.SIGNAL('clicked()'),self.goPrev)
        self.connect(self.check,QtCore.SIGNAL('clicked()'),self.onChange)
        self._update()
    
    def onChange(self):
        if self.check.isChecked():
            self.selected[self.index]=True
        else:
            self.selected[self.index]=False

    def _update(self):
        self.fitter.setBees(self.beesList[self.index])
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
        self.label.setText(str(self.index+1)+"/"+str(len(self.beesList)))

    def goNext(self):
        if self.index==len(self.beesList)-1:
            self.done(1)
        else:
            self.index+=1
        self._update()
    
    def goPrev(self):
        self.index-=1
        self._update()


def selectBees(beesList):
    a=BeesSelector(beesList)
    a.exec_()
    beesList=np.array(beesList)
    return beesList[np.array(a.selected)]

def selectFile(folder = None, filter = None, selected_filter = None):
    filename = QtGui.QFileDialog.getOpenFileName(directory = folder, 
                        filter = filter, selectedFilter = selected_filter)
    return filename

def open3ds(filename = None, folder = None):
    if filename == None:
        filename = selectFile(folder=folder, filter=u'3ds (*.3ds)')
    return gridFrom3ds(filename)
    
def findConfig():
    if os.name == 'posix':
        folder = os.path.expanduser(u'~/.pybeem')
    elif os.name == 'nt':
        folder = os.path.expandvars(u'%APPDATA%/pybeem')
    else:
        raise Exception(u"Don't know where to save config. OS unknown")
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + u'/pybeem.conf'

def savePref(filename = None):
    if filename == None:
        filename = findConfig()
    fid = open(filename,'w')
    json.dump(PREF,fid)
    fid.close()

def loadPref(filename = None):
    global PREF
    if filename == None:
        filename = findConfig()
    if os.path.exists(filename):
        fid = open(filename,'r')
        PREF.update(json.load(fid))
        fid.close()

def fitFile(filename = None, folder = None):
    if folder == None:
        folder = PREF[u'work_folder']
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
    loadPref()
    print(PREF)
