#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 14:00:12 2012

@author: Guillaume Poulin
"""




import pyqtgraph as pg
import numpy as np
        
class BEESFit_graph(object):
    
    def __init__(self):
        self.graph = pg.PlotWidget()
        ploti=self.graph.getPlotItem()
        self.label = pg.TextItem(anchor=(1,0))
        ploti.setLabel('left','BEEM Current','A')
        ploti.setLabel('bottom','Bias','V')
        self.region=pg.LinearRegionItem([0,1])
        self.region.sigRegionChanged.connect(self.fit)
        ploti.sigRangeChanged.connect(self.updatePos)
        ploti.addItem(self.region)
        ploti.addItem(self.label)
        self.cara=ploti.plot([np.nan],[np.nan])
        self.fitted=ploti.plot([np.nan],[np.nan],pen='r')
        self.graph.show()
    
    def updatePos(self):
        ploti=self.graph.getPlotItem()
        geo=ploti.viewRange()
        x=geo[0][1]
        y=geo[1][1]
        self.label.setPos(x,y)
    
    def updateBEEM(self):
        self.cara.setData(self.beesfit.bias,self.beesfit.i_beem)
    
    def updateFitted(self):
        try:
            r=np.sqrt(self.beesfit.r_squared)
            if np.isnan(r):
                r=0
            if not(self.beesfit.barrier_height==None):
                self.label.setText("Vbh=%0.5f, R=%0.5f" % (self.beesfit.barrier_height,r))
            
            if self.beesfit.i_beem_estimated==None:
                self.fitted.setData([np.nan],[np.nan])
            else:
                self.fitted.setData(self.beesfit.bias_fitted,self.beesfit.i_beem_estimated)
                
        except:
            pass
    
    def fit(self):
        Vmin,Vmax=self.region.getRegion()
        self.beesfit.bias_max=Vmax
        self.beesfit.bias_min=Vmin
        self.beesfit.fit()
        self.updateFitted()
       
            
    def set_bees(self,beesfit):
        self.beesfit=beesfit
        self.region.setRegion([beesfit.bias_min,beesfit.bias_max])
        self.updateBEEM()
        self.updateFitted()
        self.graph.getPlotItem().autoRange()
        
def select_bees(bees_fit_list):
    ui=BEESFit_graph()
    selected=[]
    i=0
    for bees in bees_fit_list:
        ui.set_bees(bees)
        print bees.barrier_height_err/bees.barrier_height
        x=raw_input("%d:"%i)
        if x=='':
            i+=1
            selected.append(bees)
    return selected