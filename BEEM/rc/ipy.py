# -*- coding: utf-8 -*-
"""
Created on Sat Jan  5 01:25:35 2013

@author: Guillaume Poulin
"""
import inspect, os, sys
sys.path.append(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))+u'../../..'))
import BEEM
import BEEM.IO as IO
import BEEM.Experiment as EXP
import BEEM.UI as UI

global BEEM=reload(BEEM)
global IO=reload(BEEM.IO)
global EXP=reload(BEEM.Experiment)
global UI=reload(BEEM.UI)
