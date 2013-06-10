#!/usr/bin/env python3
from distutils.core import setup, Extension
import numpy.distutils.misc_util


extC=Extension("beem._pure_c", ["beem/pure_c.c"],
        include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs())


setup(name='pyBEEM',
      version='0.1',
      description='BEEM analyzer program',
      author='Guillaume Poulin',
      url="https://github.com/gpoulin/pybeem",
      ext_modules=[extC],
)
