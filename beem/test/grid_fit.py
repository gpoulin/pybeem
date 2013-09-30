from beem.io import grid_from_3ds

def test_fit():
    a=grid_from_3ds('/disk/Dropbox/nus/master/BEEM/2012-12-26/Grid_HfO-3_D3_009.3ds')
    a.normal_fit()
    a.update_dict()
    a.fit(-1)

if __name__ == "__main__":
    test_fit()
