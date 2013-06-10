"""
File to update environment when working with ipython.
Simply execute "run "enviro.py"
"""

import glob
import pickle
from imp import reload

import beem
import beem.io as io
import beem.experiment as exp
import beem.ui as ui

beem=reload(beem)
io=reload(beem.io)
exp=reload(beem.experiment)
ui=reload(beem.ui)
 
