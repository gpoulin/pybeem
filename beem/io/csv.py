from beem.experiment import MODE, BEEM_MODEL
import numpy as np
from os import mkdir
from os.path import join

def bees2csv(filename,bees):
    
    if hasattr(bees,'barrier_height'):
        #it's a BEESFit
        bh = bees.barrier_height
        r = bees.trans_r
        off = bees.noise
        bh_err = bees.barrier_height_err
        r_err = bees.trans_r_err
        off_err = bees.noise_err
        n = bees.n
        R2 = bees.r_squared
        model = None
        if bees.method==BEEM_MODEL['bkv']:
            model = 'Bell-Kaiser (V correction)'
    else:
        #it's a BEESData
        bh = None
        r = None
        off = None
        bh_err = None
        r_err = None
        off_err = None
        model = None
        n = None
        R2 = None

    if bees.mode == MODE['fwd']:
        mode = 'forward'
    else:
        mode = 'backward'

    head='''BEES DATA
[METADATA]
position x : {b.pos_x}
position y : {b.pos_y}
index x : {b.x_index}
index y : {b.y_index}
sweep : {b.number}
pass : {b.pass_number}
direction : {mode}
date : {b.date}
[FIT PARAMETER]
model : {model}
n : {n}
[FITTED RESULT]
offset : {off}
barrier height : {bh}
Transmission R : {r}
offset error : {off}
barrier height error : {bh}
Transmission R error : {r}
R squared : {R2}
[DATA]
bias;i_beem;i_beem_fitted;i_tunnel;z'''.format(b=bees, bh=bh, r=r, off=off,
            mode=mode, model=model, n=n, R2=R2, bh_err=bh_err, r_err=r_err,
            off_err=off_err)

    data=np.ones((len(bees.bias),5))*np.nan
    data[:,0]=bees.bias
    data[:,1]=bees.i_beem
    data[:,3]=bees.i_tunnel
    data[:,4]=bees.pos_z

    if hasattr(bees,'i_beem_estimated'):
        data[np.in1d(bees.bias,bees.bias_fitted),2]=bees.i_beem_estimated

    np.savetxt(filename, data, delimiter=';', header=head, comments='')

def grid2csv(folder,grid,mode='good',r2=0.6):
    if mode=='data':
        liste=grid.bees
    elif mode=='fit':
        grid.beesfit
    else:
        liste=grid.extract_good(r2)

    head='''GRID DATA
[METADATA]
position x : {b.pos_x}
position y : {b.pos_y}
size x : {b.size_x}
size y : {b.size_y}
dimension x : {b.num_x}
dimension y : {b.num_y}
date : {b.date}
[DATA]
no;index x;index y;sweep;pass;direction (fwd=0, bwd=1);offset;barrier height;R'''.format(b=grid)

    data=np.ones((len(liste),9))*np.nan
    mkdir(folder)
    for i in xrange(len(liste)):
        b = liste[i]
        data[i,0] = i
        data[i,1] = b.x_index
        data[i,2] = b.y_index
        data[i,3] = b.number
        data[i,4] = b.pass_number
        data[i,5] = b.mode
        if not(mode=='data'):
            data[i,6] = b.noise
            data[i,7] = b.barrier_height[0]
            data[i,8] = b.trans_r[0]
        bees2csv(join(folder, 'bees_%04d.csv' % i),b)

    np.savetxt(join(folder,'grid.csv'),data,
            fmt=['%d','%d','%d','%d','%d','%d','%e','%.4f','%.4f'],
            delimiter=';', header=head, comments='')
