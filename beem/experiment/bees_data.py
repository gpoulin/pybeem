from .experiment import Experiment, MODE

class BEESData(Experiment):

    def __init__(self, bias=None, i_tunnel=None, i_beem=None,
                 pos_z=None, mode=MODE['fwd'], number=1, **kwds):

        super().__init__(**kwds)
        self.bias = bias
        self.i_tunnel = i_tunnel
        self.i_beem = i_beem
        self.pos_z = pos_z
        self.mode = mode
        self.number = number
        self.pass_number = -1
        self.x_index = -1
        self.y_index = -1
        self.id = None
        self.parent = None

    def __eq__(self,other):
        if other is None:
            return -1
        if self.id is None:
            self.set_id()
        elif other.id is None:
            other.set_id()
        return self.id==other.id

    def __ne__(self,other):
        return not(self==other)
    
    def __lt__(self,other):
        if other is None:
            return -1
        if self.id is None:
            self.set_id()
        elif other.id is None:
            other.set_id()
        return self.id<other.id

    def set_id(self):
        self.id = BEESID()
        self.id.x_index = self.x_index
        self.id.y_index = self.y_index
        self.id.mode = self.mode
        self.id.number = self.number
        self.id.pass_number = self.pass_number

class BEESID(object):

    def __init__(self):
        self.x_index = 0
        self.y_index = 0
        self.pass_number = 0
        self.number = 0
        self.mode = MODE['fwd']

    def __hash__(self):
        return int(self.mode + 10*self.number + 1000*self.pass_number +\
                   100000*self.y_index + 100000000*self.x_index)

    def __eq__(self,other):
        l=['x_index', 'y_index', 'pass_number', 'number', 'mode']
        for x in l:
            if self.__getattribute__(x)!=other.__getattribute__(x):
                return False
        return True

    def __ne__(self,other):
        return not(self==other)

    def __lt__(self,other):
        l=['x_index', 'y_index', 'pass_number', 'number', 'mode']
        for x in l:
            if self.__getattribute__(x)<other.__getattribute__(x):
                return True
        return False


    def copy(self):
        k = BEESID()
        k.x_index = self.x_index
        k.y_index = self.y_index
        k.pass_number = self.pass_number
        k.number = self.number
        k.mode = self.mode
        return k

    def switch_mode(self):
        k = self.copy()

        if k.mode==MODE['fwd']:
            k.mode = MODE['bwd']
        
        elif k.mode==MODE['bwd']:
            k.mode = MODE['fwd']

        return k

    def next_sweep(self):
        k = self.copy()
        k.number += 1
        return k

    def previous_sweep(self):
        k = self.copy()
        k.number -= 1
        return k


    def __str__(self):
        return '%03d_%03d_%03d_%03d_%02d'%(self.x_index, 
                                           self.y_index,
                                           self.pass_number, 
                                           self.number, 
                                           self.mode)
