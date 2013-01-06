#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 14:00:12 2012

@author: Guillaume Poulin
"""



from spyderlib.widgets.internalshell import InternalShell
import sys
from spyderlib.qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import os.path
import experiment


class IV_UI(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.initUI()
        
        
    def initUI(self):
        self.graph=pg.PlotWidget()
        ploti=self.graph.getPlotItem()
        ploti.setLabel('left','Current','A')
        ploti.setLabel('bottom','Bias','V')
        ploti.setLogMode(False,True)
        ploti.setXRange(-0.5,1.5)
        self.region=pg.LinearRegionItem([0.1,0.4])
        self.region.sigRegionChanged.connect(self.fit)
        ploti.addItem(self.region)
        self.cara=ploti.plot()
        self.fitted=ploti.plot(pen='r')
        
         # Create the console widget
        font = QtGui.QFont("Courier new")
        font.setPointSize(10)
        ns = {'win': self}
        msg = "Debug"
        self.console = cons = InternalShell(self, namespace=ns, message=msg)
        
        cons.set_font(font)
        cons.set_codecompletion_auto(True)
        cons.set_calltips(True)
        cons.setup_calltips(size=600, font=font)
        cons.setup_completion(size=(300, 180), font=font)
        self.file_btn=QtGui.QPushButton()
        self.file_btn.setIcon(QtGui.QIcon.fromTheme('folder'))
        self.file_btn.clicked.connect(self.browse)
        
        self.file_text=QtGui.QLineEdit()
        
        self.hbox1=QtGui.QHBoxLayout()
        self.hbox1.addWidget(self.file_text)
        self.hbox1.addWidget(self.file_btn)
        self.vbox=QtGui.QVBoxLayout()
        self.vbox.addLayout(self.hbox1)
        self.hbox=QtGui.QHBoxLayout()
        self.hbox.addLayout(self.vbox)
        self.hbox.addWidget(self.graph)
        self.vbox1=QtGui.QVBoxLayout()
        self.vbox1.addLayout(self.hbox)
        self.vbox1.addWidget(self.console)
        self.setLayout(self.vbox1)
        
    def browse(self):
        f=str(self.file_text.text())
        d=os.path.dirname(f)
        if not(os.path.isdir(d)):
            d=os.path.expanduser("~")
        fname= QtGui.QFileDialog.getOpenFileName(self,self.tr('Choose a file'),d)
        self.file_text.setText(fname)
        self.iv=experiment.iv.fromfile(fname)     
        ploti=self.graph.getPlotItem()
        self.cara.setData(self.iv.V,np.abs(self.iv.I))
        self.fit()
        ploti.enableAutoScale()
        
        
    def fit(self):
        Vmin,Vmax=self.region.getRegion()
        self.iv.Vmax=Vmax
        self.iv.Vmin=Vmin
        V=np.linspace(Vmin,Vmax,300)
        I=self.iv.Ifitted(V)
        self.fitted.setData(V,np.abs(I))
        

def main():
    app = QtGui.QApplication(sys.argv)
    wid = QtGui.QMainWindow()
    wid.resize(1000, 700)
    wid.setWindowTitle('pyBEEM')
    wid.setCentralWidget(IV_UI())
    wid.show()
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":
    main()