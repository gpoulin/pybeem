from .ui import QtGui
import pyqtgraph as pg
import numpy as np

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
        self.bees_list=bees_list
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
        self.check.stateChanged.connect(self.on_change)
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
        elif self.index==len(self.bees_list)-1:
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
