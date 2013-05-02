# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 01:25:35 2013

@author: Guillaume Poulin
"""
import inspect, os, sys
sys.path.append(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))+u'../../..'))
from BEEM.IO import *
from BEEM.Experiment import *
from pylab import *
from BEEM.UI import *
load_pref()
ion()