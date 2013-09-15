PyBEEM
======

Python program to handle data produced during Ballistic Emission Electron
Microscopy (Mainly BEES fitting).

Contributors
------------

###Main developer
  * Guillaume Poulin poulin.guillaume@gmail.com

Dependencies
------------

###Mandatory dependencies
  * python >=3.3
  * matplotlib >=1.2
  * NumPy >=1.6
  * Scipy >=0.11

###For graphic interface
  * PyQt >=4.9
  * PyQtGraph >=0.9.8

###For interactive console
  * IPython


Install
-------
  * set CFLAFS (optional):
    `export CFLAGS='-O3 -mtune=native -march=native'`

  * install system:
    `python setup.py install`
    
  * install inplace:
    `python setup.py build --buid-lib .`
