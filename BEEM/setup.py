#!/usr/bin/env python3
from distutils.core import setup, Extension
import numpy.distutils.misc_util


extC=Extension("_pureC", ["pureC.c"],include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs())


setup(
  ext_modules=[extC],
)
