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


_pref = dict()


def select_file(folder = None, filter = None):
    filename = QtGui.QFileDialog.getOpenFileNames(directory = folder,
                        filter = filter)
    return filename

def open3ds(filename = None, folder = None):
    if filename == None:
        filename = select_file(folder=folder, filter=u'3ds (*.3ds)')
        for f in filename:
            try:
                a = a + grid_from_3ds(f)
            except:
                a = grid_from_3ds(f)
    return a

def find_config():
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

def main(arg):
    pass
