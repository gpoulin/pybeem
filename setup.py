#!/usr/bin/env python3
from distutils.core import setup, Extension
import numpy.distutils.misc_util
from distutils.command.build_py import build_py
from distutils.command.build import build
from distutils.command.clean import clean
import sys
import os
import glob

extC = Extension(
                "beem.experiment._pure_c", ["beem/experiment/pure_c.c"],
                include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs()
                )

class my_build(build_py):
    def run(self):
        from PyQt4 import QtCore
        pyuic = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.BinariesPath)
        pyuic = os.path.join(pyuic, 'pyuic4')
        folder = os.path.join(self.build_lib, 'beem/ui')
        self.mkpath(folder)
        for f in glob.glob('ui/*.ui'):
            out = os.path.join(folder,
                    os.path.splitext(os.path.basename(f))[0] + '_ui.py')
            print('creating ' + out)
            os.system(pyuic + ' ' + f + ' -o ' + out)
        build_py.run(self)


class my_clean(clean):
    def run(self):
        clean.run(self)
        for f in glob.glob('beem/*.so') + glob.glob('beem/ui/*_ui.py'):
            print('removing ', f)
            os.remove(f)



setup(name = 'pyBEEM',
      version = '0.1',
      description = 'BEEM analyzer program',
      author = 'Guillaume Poulin',
      author_email = 'guillaume.poulin@gmail.com',
      url = "https://github.com/gpoulin/pybeem",
      ext_modules = [extC],
      license = 'GPLv3',
      packages = ['beem','beem.ui'],
      cmdclass = {'build_py': my_build, 'clean': my_clean},
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: C',
          'Topic :: Scientific/Engineering :: Physics',
          ],
)
