from distutils.core import setup, Extension
import numpy.distutils.misc_util
from Cython.Distutils import build_ext


ext=Extension("_cython", ["_cython.pyx"],include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs())
extC=Extension("_pureC", ["pureC.c"],include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs())


setup(
  ext_modules=[ext,extC],
  cmdclass = {'build_ext': build_ext}
)
