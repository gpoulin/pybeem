"""
Created on Sat Jan  5 00:44:47 2013

@author: Guillaume Poulin
"""

import numpy as np

from .iv import IV
from .grid import Grid
from .bees_data import BEESData
from .bees_fit import BEESFit

_use_pure_c=True
bell_kaiser_v=None
residu_bell_kaiser_v=None

def use_pure_c(val=True):
    global bell_kaiser_v,residu_bell_kaiser_v,_use_pure_c
    if val==True:
        try:
            bell_kaiser_v=_pure_c.bell_kaiser_v
            residu_bell_kaiser_v=_pure_c.residu_bell_kaiser_v
            _use_pure_c = True
            return
        except:
            pass

    from . import _pure_python as _pure_python
    bell_kaiser_v = _pure_python.bell_kaiser_v
    residu_bell_kaiser_v = _pure_python.residu_bell_kaiser_v
    _use_pure_c = False


try:
  from . import _pure_c as _pure_c
  use_pure_c(True)
except ImportError:
  use_pure_c(False)
