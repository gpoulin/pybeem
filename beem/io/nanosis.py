import numpy as np
import datetime
from beem.experiment import BEESData, Grid, IV, MODE

def _file2data(filename, lastHeader="[DATA]"):
    """Function to read data from ASCII file with header

    Args:
        filename (str): location of the file to be read
        lastHeader (str): value of the last header line
    """

    fid = open(filename,"rb")
    line = fid.readline().decode('utf_8')
    dico = {}

    while line.rstrip()!=lastHeader:
        split_line = line.split()
        if not(not(split_line)):
            dico.update({
            'Date': lambda x: {'date' : datetime.datetime.strptime(
                    x[1] + ' ' + x[2], '%d.%m.%Y %H:%M:%S')},
            'X': lambda x: {'pos_x': np.double(x[2])},
            'Y': lambda x: {'pos_y': np.double(x[2])},
            }.get(split_line[0],lambda x: {})(split_line))

        line = fid.readline().decode('utf_8')

    line=fid.readline().decode('utf_8')
    header_list=line.rstrip().split('\t')
    name=dict(zip(header_list, range(len(header_list))))

    data=np.genfromtxt(fid)

    fid.close()

    return data, name, dico

def bees_from_file(filename,dic={'beem':'BEEM Current'}):
    data, name, dico = _file2data(filename)
    BEES=[]
    if 'BEEM Current (A)' in name:
        BEES.append(BEESData(
            bias = data[:,name['Bias (V)']],
            i_beem = data[:,name['BEEM Current (A)']],
            i_tunnel = data[:,name['Current (A)']],
            pos_z = data[:,name['Z (m)']],
            mode=MODE['fwd'],**dico))

        BEES.append(BEESData(
            bias = data[:,name['Bias [bwd] (V)']],
            i_beem = data[:,name['BEEM Current [bwd] (A)']],
            i_tunnel = data[:,name['Current [bwd] (A)']],
            pos_z = data[:,name['Z [bwd] (m)']],
            mode=MODE['bwd'],**dico))

    else:
        i=1
        while 'Bias [%05i] (V)'%i in name:
            BEES.append(BEESData(
                bias = data[:,name['Bias [%05i] (V)'%i]],
                i_beem = data[:,name[dic['beem']+ ' [%05i] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] (A)'%i]],
                pos_z = data[:,name['Z [%05i] (m)'%i]],
                mode=MODE['fwd'], number=i, **dico))

            BEES.append(BEESData(
                bias = data[:,name['Bias [%05i] [bwd] (V)'%i]],
                i_beem = data[:,name[dic['beem']+' [%05i] [bwd] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] [bwd] (A)'%i]],
                pos_z = data[:,name['Z [%05i] [bwd] (m)'%i]],
                mode=MODE['bwd'], number=i, **dico))

            i+=1

    return BEES


def grid_from_files(filenames, dic=None):
    g = Grid()
    for f in filenames:
        if dic==None:
            b = bees_from_file(f)
        else:
            b = bees_from_file(f, dic)
        g.bees += b
    return g


def _iv_from_file(filename,dic={}):
    if not('Current' in dic):
        dic['Current']='IV Current'
    data,name,other=_file2data(filename)
    a=[IV(),IV()]
    a[0].V=data[:,name['Bias (V)']]
    a[1].V=data[:,name['Bias [bwd] (V)']]
    a[0].I=data[:,name[dic['Current'] + ' (A)']]
    a[1].I=data[:,name[dic['Current'] + ' [bwd] (A)']]
    a[1].mode=MODE['bwd']
    return a

def iv_from_file(filenames, dic={}):
    list = []
    if not isinstance(filename,list):
        filename = [filename]
    for filename in filenames:
        list += iv_from_file(filename,dic)
    return list

