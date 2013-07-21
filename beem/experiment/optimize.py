"""Module that redifine leastsq from scipy.optimize to remove some slow 
verifications.
"""

import scipy.optimize as op
from scipy.linalg.lapack import get_lapack_funcs
from scipy.linalg import calc_lwork
from numpy.linalg import LinAlgError
getrf, getri = get_lapack_funcs(('getrf','getri'), (np.eye(3),))

def inv(a):
    global getrf, getri
    lu, piv, info = getrf(a, overwrite_a=True)
    if info == 0:
        lwork = calc_lwork.getri(getri.typecode, a.shape[0])
        lwork = lwork[1]
        lwork = int(1.01 * lwork)
        inv_a, info = getri(lu, piv, lwork=lwork, overwrite_lu=1)
    if info > 0:
        raise LinAlgError("singular matrix")
    if info < 0:
        raise ValueError('illegal value in %d-th argument of internal '
                                                    'getrf|getri' % -info)
    return inv_a


def leastsq(func,p0,args,full_output):
    n=len(p0)
    retval = op._minpack._lmdif(func, p0, args, 1, 1.49012e-8, 1.49012e-8,
                                 0.0, 2000, 1.49012e-8, 100.0, None)
    info = retval[-1]
    cov_x = None
    if info in [1, 2, 3, 4]:
        perm = np.take(np.eye(n), retval[1]['ipvt'] - 1, 0)
        r = np.triu(np.transpose(retval[1]['fjac'])[:n, :])
        R = np.dot(r, perm)
        try:
            cov_x = inv(np.dot(np.transpose(R), R))
        except (LinAlgError, ValueError):
            pass
    return retval[0], cov_x

