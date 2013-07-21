import gzip
import pickle

def save_space(filenames, space, comp=True):
    if comp:
        f = gzip.open(filenames,'wb')
    else:
        f = open(filenames,'wb')
    pickle.dump(space, f, protocol=3)
    f.close()

def load_space(filenames):
    try:
        f = gzip.open(filenames, 'rb')
        a=pickle.load(f)
    except IOError:
        f.close()
        f=open(filenames, 'rb')
        a=pickle.load(f)
    f.close()
    return a
