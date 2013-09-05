import numpy as np
import datetime
from beem.experiment import Grid, BEESData
from beem.experiment.experiment import MODE

CHANNEL_NAME={
        'beem':'BEEM Current',
        'tunnel':'Current',
        'bias':'Bias',
        'z':'Z'
        }

def grid_from_3ds(filename, channel_name={}):
    """Create a grid object from one or many 3ds files
    """
    if not isinstance(filename, list):
        filename = [filename]

    grid = Grid()
    for x in filename:
        grid += _grid_from_3ds(x, channel_name)

    return grid

def _grid_from_3ds(filename, channel={}):
    fid = open(filename, 'rb')
    grid = Grid()
    line = fid.readline().decode('utf_8').strip()
    grid.src_file = filename
    param_list = []
    channel_name = CHANNEL_NAME.copy()
    channel_name.update(channel)

    while line!=':HEADER_END:':
        splited = line.split('=')

        if not(splited):
            continue

        param = splited[0].strip()
        value = splited[1].strip()

        if param=='Grid dim':
            value = value.strip('"')
            value = value.split('x')
            grid.num_x = int(value[0].strip())
            grid.num_y = int(value[1].strip())

        elif param=='Grid settings':
            value = [float(x.strip()) for x in value.split(';')]
            grid.pos_x = value[0]
            grid.pos_y = value[1]
            grid.size_x = value[2]
            grid.size_y = value[3]

        elif param=='Fixed parameters':

            value = [x.strip() for x in value.strip('"').split(';')]
            for channel in value:
                param_list.append(channel)

        elif param=='Experiment parameters':
            value = [x.strip() for x in value.strip('"').split(';')]
            for channel in value:
                param_list.append(channel)

        elif param=='Points':
            points = int(value)

        elif param=='Channels':
            channel_list = [x.strip() for x in value.strip('"').split(';')]

        elif param=='Date':
            grid.date = datetime.datetime.strptime(value.strip('"'),
                                                   '%d.%m.%Y %H:%M:%S')

        line=fid.readline().decode('utf_8').strip()


    param_num = len(param_list)
    length = len(channel_list)*points+param_num
    param_dict = dict(zip(param_list,range(0,len(param_list))))
    channel_dict = dict(zip(channel_list,range(0,len(channel_list))))


    data=fid.read()
    fid.close()

    #Test if all the data is there
    if len(data)==length*grid.num_x*grid.num_y*4:
        grid.completed = True
        num = grid.num_x*grid.num_y
    else:
        grid.completed=False
        num=len(data)//length//4

    #Transform the data from 32bits Big Endian to 64bits Little Endian
    data=np.array(np.ndarray(shape=(length*num,), dtype='>f4', buffer=data),
                  dtype='<f8')

    for i in range(num):
        delta = i*length
        pos_x = data[delta+param_dict['X (m)']]
        pos_y = data[delta+param_dict['Y (m)']]
        dico = {'pos_x':pos_x,
                'pos_y':pos_y,
                'date':grid.date,
                'src_file':grid.src_file
                }

        if channel_name['tunnel'] + ' (A)' in channel_dict :
            grid.bees.append(BEESData(
            bias = data[delta+param_num+channel_dict['Bias (V)']*points:param_num+channel_dict['Bias (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current (A)']*points:param_num+channel_dict['BEEM Current (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current (A)']*points:param_num+channel_dict['Current (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z (m)']*points:param_num+channel_dict['Z (m)']*points+points+delta:],
            mode=MODE['fwd'],**dico))

            grid.bees.append(BEESData(
            bias = data[delta+param_num+channel_dict['Bias [bwd] (V)']*points:param_num+channel_dict['Bias [bwd] (V)']*points+points+delta:],
            i_beem = data[delta+param_num+channel_dict['BEEM Current [bwd] (A)']*points:param_num+channel_dict['BEEM Current [bwd] (A)']*points+points+delta:],
            i_tunnel = data[delta+param_num+channel_dict['Current [bwd] (A)']*points:param_num+channel_dict['Current [bwd] (A)']*points+points+delta:],
            pos_z = data[delta+param_num+channel_dict['Z [bwd] (m)']*points:param_num+channel_dict['Z [bwd] (m)']*points+points+delta:],
            mode=MODE['bwd'],**dico))


    return grid
