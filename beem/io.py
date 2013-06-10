"""
Created on Fri Dec  7 18:43:57 2012

@author: Guillaume Poulin
"""

import numpy as np
import datetime
from beem import experiment


def file2data(filename, lastHeader="[DATA]"):
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

def scan2data(filename):
    f=file(filename,'rb')
    s=f.readline()
    s=s.rstrip()

    while s!=b":SCANIT_END:":
        if s==b":DATA_INFO:":
            s=f.readline()


    s=f.read(2)
    while s!=b'\x1a\x04':
        s[0]=s[1]
        s[1]=f.read(1)


def BEESFromFile(filename,dic={'beem':'BEEM Current'}):
    data, name, dico = file2data(filename)
    BEES=[]
    if 'BEEM Current (A)' in name:
        BEES.append(experiment.BEESData(
            bias = data[:,name['Bias (V)']],
            i_beem = data[:,name['BEEM Current (A)']],
            i_tunnel = data[:,name['Current (A)']],
            pos_z = data[:,name['Z (m)']],
            mode=experiment.MODE['fwd'],**dico))

        BEES.append(experiment.BEESData(
            bias = data[:,name['Bias [bwd] (V)']],
            i_beem = data[:,name['BEEM Current [bwd] (A)']],
            i_tunnel = data[:,name['Current [bwd] (A)']],
            pos_z = data[:,name['Z [bwd] (m)']],
            mode=experiment.MODE['bwd'],**dico))

    else:
        i=1
        while 'Bias [%05i] (V)'%i in name:
            BEES.append(experiment.BEESData(
                bias = data[:,name['Bias [%05i] (V)'%i]],
                i_beem = data[:,name[dic['beem']+ ' [%05i] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] (A)'%i]],
                pos_z = data[:,name['Z [%05i] (m)'%i]],
                mode=experiment.MODE['fwd'], number=i, **dico))

            BEES.append(experiment.BEESData(
                bias = data[:,name['Bias [%05i] [bwd] (V)'%i]],
                i_beem = data[:,name[dic['beem']+' [%05i] [bwd] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] [bwd] (A)'%i]],
                pos_z = data[:,name['Z [%05i] [bwd] (m)'%i]],
                mode=experiment.MODE['bwd'], number=i, **dico))

            i+=1

    return BEES


def grid_from_files(filenames,dic=None):
    g=experiment.Grid()
    for f in filenames:
        if dic==None:
            b=BEESFromFile(f)
        else:
            b=BEESFromFile(f,dic)
        g.bees+=b
    return g


def grid_from_3ds(filename):
    fid=open(filename,'rb')
    grid=experiment.Grid()
    line=fid.readline().decode('utf_8').strip()
    grid.src_file=filename
    param_list=[]

    while line!=':HEADER_END:':
        splited=line.split('=')

        if not(splited):
            continue

        param=splited[0].strip()
        value=splited[1].strip()

        if param=='Grid dim':
            value=value.strip('"')
            value=value.split('x')
            grid.num_x=int(value[0].strip())
            grid.num_y=int(value[1].strip())

        elif param=='Grid settings':
            value=[float(x.strip()) for x in value.split(';')]
            grid.pos_x=value[0]
            grid.pos_y=value[1]
            grid.size_x=value[2]
            grid.size_y=value[3]

        elif param=='Fixed parameters':
            value=[ x.strip() for x in value.strip('"').split(';')]
            for channel in value:
                param_list.append(channel)

        elif param=='Experiment parameters':
            value=[ x.strip() for x in value.strip('"').split(';')]
            for channel in value:
                param_list.append(channel)

        elif param=='Points':
            points=int(value)

        elif param=='Channels':
            channel_list=[ x.strip() for x in value.strip('"').split(';')]

        elif param=='Date':
            grid.date=datetime.datetime.strptime(value.strip('"'),'%d.%m.%Y %H:%M:%S')

        line=fid.readline().decode('utf_8').strip()


    param_num=len(param_list)
    length=len(channel_list)*points+param_num
    param_dict=dict(zip(param_list,range(0,len(param_list))))
    channel_dict=dict(zip(channel_list,range(0,len(channel_list))))


    data=fid.read()
    fid.close()

    if len(data)==length*grid.num_x*grid.num_y*4:
        grid.completed=True
        num=grid.num_x*grid.num_y
    else:
        grid.completed=False
        num=len(data)//length//4

    data=np.array(np.ndarray(shape=(length*num,),dtype='>f4', buffer=data),dtype='<f8')

    for i in range(num):
        delta=i*length
        pos_x=data[delta+param_dict['X (m)']]
        pos_y=data[delta+param_dict['Y (m)']]
        dico={'pos_x':pos_x, 'pos_y':pos_y, 'date':grid.date, 'src_file':grid.src_file}

        if 'BEEM Current (A)' in channel_dict :
            grid.bees.append(experiment.BEESData(
            bias = data[delta+param_num+channel_dict['Bias (V)']*points:param_num+channel_dict['Bias (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current (A)']*points:param_num+channel_dict['BEEM Current (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current (A)']*points:param_num+channel_dict['Current (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z (m)']*points:param_num+channel_dict['Z (m)']*points+points+delta:],
            mode=experiment.MODE['fwd'],**dico))

            grid.bees.append(experiment.BEESData(
            bias = data[delta+param_num+channel_dict['Bias [bwd] (V)']*points:param_num+channel_dict['Bias [bwd] (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current [bwd] (A)']*points:param_num+channel_dict['BEEM Current [bwd] (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current [bwd] (A)']*points:param_num+channel_dict['Current [bwd] (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z [bwd] (m)']*points:param_num+channel_dict['Z [bwd] (m)']*points+points+delta:],
            mode=experiment.MODE['bwd'],**dico))


    return grid


def iv_from_file(filename,dic={}):
    if not('Current' in dic):
        dic['Current']='IV Current'
    data,name,other=file2data(filename)
    a=[experiment.IV(),experiment.IV()]
    a[0].V=data[:,name['Bias (V)']]
    a[1].V=data[:,name['Bias [bwd] (V)']]
    a[0].I=data[:,name[dic['Current'] + ' (A)']]
    a[1].I=data[:,name[dic['Current'] + ' [bwd] (A)']]
    a[1].mode=experiment.MODE['bwd']
    return a

def ivs_from_file(filenames,dic={}):
    list=[]
    for filename in filenames:
        list+=iv_from_file(filename,dic)
    return list

if __name__ == "__main__":
    g=grid_from_3ds('/run/media/guillaume/D4D0-B7A7/2013-04-22/Grid Spectroscopy_Au-sp5-w5_C2_001.3ds')
    g.init_grid()
    g.normal_fit()
    experiment.use_pure_c(True)
    g.fit(2)
