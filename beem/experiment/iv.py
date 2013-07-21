import numpy as np
import scipy.optimize as op
import scipy.constants as constants

from .experiment import Experiment
from . import r_squared

class IV(Experiment):

    def __init__(self,**kwd):
        super(IV,self).__init__(**kwd)
        self.V = np.array([])
        self.I = np.array([])
        self.mode = MODE['fwd']
        self.T = 300.0
        self.A = 1.1e6
        self.W = np.pi*2.5e-4**2
        self.n = 0
        self.barrier_height = 0
        self.r_squared = 0
        self.Vmax = 0
        self.Vmin = 0
        self.KbT = constants.physical_constants['Boltzmann constant in eV/K'][0]\
                *self.T
        self.Is = self.A*self.W*self.T**2

    @property
    def _fit_index(self):
        return np.logical_and(self.V<self.Vmax,self.V>self.Vmin)

    @property
    def V_fitted(self):
        return self.V[self._fit_index]

    @property
    def I_fitted(self):
        return self.I[self._fit_index]

    @staticmethod
    def schottky_richardson(V,Vbh,n,Is,KbT):
        I=Is*np.exp(-Vbh/(KbT)+V/(n*KbT))*(1-np.exp(-V/(KbT)))
        return I

    def _model_fit(self,V,Vbh,n):
        return np.log(np.abs(IV.schottky_richardson(V,Vbh,n,self.Is,self.KbT)))

    def fit(self,Vbh_init=0.8,n_init=1.0):
        popt,pconv=op.curve_fit(self._model_fit,self.V_fitted,
                np.log(np.abs(self.I_fitted)),[Vbh_init,n_init])
        self.barrier_height = popt[0]
        self.n = popt[1]
        self.r_squared = r_squared(np.log(np.abs(self.I_fitted)),
                self._model_fit(self.V_fitted,popt[0],popt[1]))

