#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 14:00:12 2012

@author: Guillaume Poulin
"""




import pyqtgraph as pg
import numpy as np
from BEEM.IO import grid_from_3ds
import os
import json

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

PREF = {
    u'work_folder':os.path.expanduser(u'~')
    
    }

class BEESFit_graph(object):

    def __init__(self):
        self.graph = pg.PlotWidget()
        ploti = self.graph.getPlotItem()
        self.label = pg.TextItem(anchor=(1, 0))
        ploti.setLabel('left', u'BEEM Current','A')
        ploti.setLabel('bottom', u'Bias','V')
        self.region = pg.LinearRegionItem([0, 1])
        self.region.sigRegionChanged.connect(self.fit)
        ploti.sigRangeChanged.connect(self.updatePos)
        ploti.addItem(self.region)
        ploti.addItem(self.label)
        self.cara = ploti.plot([np.nan], [np.nan])
        self.fitted = ploti.plot([np.nan], [np.nan], pen='r')
        self.graph.show()
        self.beesfit = None

    def updatePos(self):
        ploti = self.graph.getPlotItem()
        geo = ploti.viewRange()
        x = geo[0][1]
        y = geo[1][1]
        self.label.setPos(x, y)

    def updateBEEM(self):
        self.cara.setData(self.beesfit.bias, self.beesfit.i_beem)

    def updateFitted(self):
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

        except:
            pass

    def fit(self):
        Vmin, Vmax = self.region.getRegion()
        self.beesfit.bias_max = Vmax
        self.beesfit.bias_min = Vmin
        self.beesfit.fit()
        self.updateFitted()


    def set_bees(self, beesfit):
        self.beesfit = beesfit
        self.region.setRegion([beesfit.bias_min, beesfit.bias_max])
        self.updateBEEM()
        self.updateFitted()
        self.graph.getPlotItem().autoRange()

def select_bees(bees_fit_list):
    ui = BEESFit_graph()
    selected = []
    i = 0
    for bees in bees_fit_list:
        ui.set_bees(bees)
        x = raw_input("%d:"%i)
        if x == '':
            i += 1
            selected.append(bees)
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
    fid = open(filename,'r')
    PREF = json.load(fid)
    fid.close()

def fit_file(filename = None, folder = None):
    if folder == None:
        folder = PREF[u'work_folder']
    g = open_3ds(filename, folder)
    g.normal_fit()
    g.fit(-1)
    return g