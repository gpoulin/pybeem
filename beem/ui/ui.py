import os
import json
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
from PyQt4 import QtGui, QtCore

signal = QtCore.pyqtSignal
slot = QtCore.pyqtSlot
property = QtCore.pyqtProperty


from beem.io import grid_from_3ds
from beem.experiment import Grid
from beem.ui.graph import contourplot


_pref = dict()


def select_file(folder = None, filter = None):
    filename = QtGui.QFileDialog.getOpenFileNames(directory = folder,
            filter = filter)
    return filename

def open3ds(filename = None, folder = None):
    """Return a Grid object from 3ds files
    """
    if filename == None:
        filename = select_file(folder = folder, filter = '3ds (*.3ds)')
        if len(filename)==0:
            return None
    for f in filename:
        try:
            a = a + grid_from_3ds(f)
        except NameError:
            a = grid_from_3ds(f)
    return a

def fast_analysis(filename = None):
    """Do the default analysis on 3ds files
    """
    grid=open3ds(filename)
    if grid==None:
        return None
    grid.normal_fit()
    grid.update_dict()
    grid.fit()
    contourplot(grid.extract_good())
    return grid


def find_config():
    """Return the location of the config and 
    create folder to store it if needed
    """
    if os.name == 'posix':
        folder = os.path.expanduser('~/.pybeem')
    elif os.name == 'nt':
        folder = os.path.expandvars('%APPDATA%/pybeem')
    else:
        raise Exception("Don't know where to save config. OS unknown")

    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder + '/pybeem.conf'

def save_pref(filename = None):
    if filename == None:
        filename = find_config()
    fid = open(filename,'w')
    json.dump(_pref,fid)
    fid.close()

def load_pref(filename = None):
    global _pref
    if filename == None:
        filename = find_config()
    if os.path.exists(filename):
        fid = open(filename,'r')
        _pref.update(json.load(fid))
        fid.close()
