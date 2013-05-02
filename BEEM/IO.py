# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 18:43:57 2012

@author: Guillaume Poulin
"""

import numpy as np
import datetime
import Experiment


def file2data(filename, lastHeader="[DATA]"):
    """Function to read data from ASCII file with header
    
    Args:
        filename (str): location of the file to be read
        lastHeader (str): value of the last header line
    """
    
    fid = open(filename,"r")
    line = fid.readline()
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
        
        line = fid.readline()
        
    
    line=fid.readline()
    header_list=line.rstrip().split('\t')
    name=dict(zip(header_list, range(0,len(header_list))))
    
    data=np.genfromtxt(fid)
    
    fid.close()
    
    return data, name, dico
    
def scan2data(filename):
    f=file(filename,'r')
    s=f.readline()
    s=s.rstrip()
    
    while s!=":SCANIT_END:":
        if s==":DATA_INFO:":
            s=f.readline()
            
        
    s=f.read(2)
    while s!='\x1a\x04':
        s[0]=s[1]
        s[1]=f.read(1)
    

def BEESFromFile(filename):
    data, name, dico = file2data(filename)
    BEES=[]
    if name.has_key('BEEM Current (A)'):
        BEES.append(Experiment.BEESData(
            bias = data[:,name['Bias (V)']],
            i_beem = data[:,name['BEEM Current (A)']],
            i_tunnel = data[:,name['Current (A)']],
            pos_z = data[:,name['Z (m)']],
            mode=Experiment.MODE['fwd'],**dico))
     
        BEES.append(Experiment.BEESData(
            bias = data[:,name['Bias [bwd] (V)']],
            i_beem = data[:,name['BEEM Current [bwd] (A)']],
            i_tunnel = data[:,name['Current [bwd] (A)']],
            pos_z = data[:,name['Z [bwd] (m)']],
            mode=Experiment.MODE['bwd'],**dico))
            
    else:
        i=1
        while name.has_key('Bias [%05i] (V)'%i):
            BEES.append(Experiment.BEESData(
                bias = data[:,name['Bias [%05i] (V)'%i]],
                i_beem = data[:,name['BEEM Current [%05i] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] (A)'%i]],
                pos_z = data[:,name['Z [%05i] (m)'%i]],
                mode=Experiment.MODE['fwd'], number=i, **dico))
         
            BEES.append(Experiment.BEESData(
                bias = data[:,name['Bias [%05i] [bwd] (V)'%i]],
                i_beem = data[:,name['BEEM Current [%05i] [bwd] (A)'%i]],
                i_tunnel = data[:,name['Current [%05i] [bwd] (A)'%i]],
                pos_z = data[:,name['Z [%05i] [bwd] (m)'%i]],
                mode=Experiment.MODE['bwd'], number=i, **dico))
            
            i+=1
        
    return BEES
    
    
def grid_from_files(filenames):
    g=Experiment.Grid()
    for f in filenames:
        b=BEESFromFile(f)
        g.bees+=b
    return g
            

def grid_from_3ds(filename):
    fid=open(filename,'rb')
    grid=Experiment.Grid()
    line=fid.readline().strip()
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
            grid.date=datetime.datetime.strptime(value.strip('"'), 
                                                 '%d.%m.%Y %H:%M:%S')
        line=fid.readline().strip()
        
        
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
        num=len(data)/length/4
        
    data=np.array(np.ndarray(shape=(length*num,),dtype='>f4', buffer=data),dtype='<f8')
    
    
    for i in range(0,num):
        delta=i*length
        pos_x=data[delta+param_dict['X (m)']]
        pos_y=data[delta+param_dict['Y (m)']]
        dico={'pos_x':pos_x, 'pos_y':pos_y, 'date':grid.date, 'src_file':grid.src_file}
        
        if channel_dict.has_key('BEEM Current (A)'):
            grid.bees.append(Experiment.BEESData(
            bias = data[delta+param_num+channel_dict['Bias (V)']*points:param_num+channel_dict['Bias (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current (A)']*points:param_num+channel_dict['BEEM Current (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current (A)']*points:param_num+channel_dict['Current (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z (m)']*points:param_num+channel_dict['Z (m)']*points+points+delta:],
            mode=Experiment.MODE['fwd'],**dico))
        
            grid.bees.append(Experiment.BEESData(
            bias = data[delta+param_num+channel_dict['Bias [bwd] (V)']*points:param_num+channel_dict['Bias [bwd] (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current [bwd] (A)']*points:param_num+channel_dict['BEEM Current [bwd] (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current [bwd] (A)']*points:param_num+channel_dict['Current [bwd] (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z [bwd] (m)']*points:param_num+channel_dict['Z [bwd] (m)']*points+points+delta:],
            mode=Experiment.MODE['bwd'],**dico))
        
    
    return grid
    
    
def iv_from_file(filename):
    data,name,other=file2data(filename)
    a=[Experiment.IV(),Experiment.IV()]
    a[0].V=data[:,name['Bias (V)']]
    a[1].V=data[:,name['Bias [bwd] (V)']]
    a[0].I=data[:,name['IV Current (A)']]
    a[1].I=data[:,name['IV Current [bwd] (A)']]
    a[1].mode=Experiment.MODE['bwd']
    return a
    
def ivs_from_file(filenames):
    list=[]
    for filename in filenames:
        list+=iv_from_file(filename)
    return list
    
if __name__ == "__main__":
    g=grid_from_3ds('/home/guillaume/Dropbox/nus/master/BEEM/2012-12-26/Grid_HfO-3_D3_009.3ds')
    g.normal_fit()
    Experiment.use_pureC(True)
    g.fit(-1)