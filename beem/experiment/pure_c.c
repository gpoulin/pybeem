#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>
#include <stdio.h>


//Header (.h)
static PyObject *bell_kaiser_v(PyObject *self, PyObject *args);
static PyObject *residu_bell_kaiser_v(PyObject *self, PyObject *args);
void _bell_kaiser_v(int leng ,double * bias, double * i_beem, double n,
        double noise, int n_barriers, double* barrier_height, double* trans_a);

//Doc of the module
static char module_docstring[] ="This module reimplement some critical "
    "function in C to increase speed.\nAll function have the same interface "
    "than their python counterpart.\nAttention: these functions doesn't "
    "implement any verification of the parameter passed. In case of bug "
    "use the python implementation to do the debugging (use_pure_c=Flase).";

//Doc of the functions
static char bell_kaiser_v_docstring[] = "See _pure_python.bell_kaiser_v.";
static char residu_bell_kaiser_v_docstring[] = "See "
    "_pure_python.residu_bell_kaiserV.";


//Definition of the function see by python
static PyMethodDef module_methods[] = {
  {"bell_kaiser_v",bell_kaiser_v, METH_VARARGS,bell_kaiser_v_docstring},
  {"residu_bell_kaiser_v",residu_bell_kaiser_v, METH_VARARGS,
      residu_bell_kaiser_v_docstring},
  {NULL,NULL,0,NULL}
};


static struct PyModuleDef _pure_c_module = {
   PyModuleDef_HEAD_INIT,
   "_pure_c",   /* name of module */
   module_docstring, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   module_methods
};


PyMODINIT_FUNC
PyInit__pure_c(void)
{
    import_array();
    return PyModule_Create(&_pure_c_module);
}


static PyObject *bell_kaiser_v(PyObject *self, PyObject *args)
{
  PyObject *bias, *i_beem, *bias_array, *params, *params_array;
  double *dparams, n;
  unsigned int l, n_barriers;
  npy_intp dim;

  //Extract argument
  if (!PyArg_ParseTuple(args, "OdO", &bias, &n, &params)) return NULL;
  bias_array = PyArray_FROM_OTF(bias, NPY_DOUBLE, NPY_IN_ARRAY);
  params_array = PyArray_FROM_OTF(params, NPY_DOUBLE, NPY_IN_ARRAY);


  //Retrieve dimension of bias and number of barrier height
  n_barriers=((int)PyArray_DIM(params_array, 0)-1)/2;
  l=(int)PyArray_DIM(bias_array, 0);
  dparams=(double*)PyArray_DATA(params_array);

  //Create an array to store the result
  dim=(npy_intp)l;
  i_beem=PyArray_EMPTY(1,&dim,NPY_DOUBLE,0);

  //Do the calcul
  _bell_kaiser_v(l,(double*)PyArray_DATA(bias_array),
          (double*)PyArray_DATA(i_beem),n ,dparams[0],n_barriers,dparams+1,
          dparams+1+n_barriers);

  //Clean Py_objects
  Py_DECREF(bias_array);
  Py_DECREF(params_array);


  //return Value
  return PyArray_Return((PyArrayObject*) i_beem);
}



static PyObject *residu_bell_kaiser_v(PyObject *self, PyObject *args)
{
  PyObject *bias, *i_beem, *res, *i_beem_array, *bias_array, *params,
           *params_array;
  double *dparams, n, *di_beem, *dres;
  int l, i, n_barriers;
  npy_intp dim;

  //Extract parameters
  if (!PyArg_ParseTuple(args, "OOOd",&params, &bias, &i_beem, &n)) return NULL;
  bias_array = PyArray_FROM_OTF(bias, NPY_DOUBLE, NPY_IN_ARRAY);
  i_beem_array = PyArray_FROM_OTF(i_beem, NPY_DOUBLE, NPY_IN_ARRAY);
  params_array = PyArray_FROM_OTF(params, NPY_DOUBLE, NPY_IN_ARRAY);

  //Get Data
  l=(int)PyArray_DIM(bias_array, 0);
  n_barriers=((int)PyArray_DIM(params_array, 0)-1)/2;
  dparams=(double*)PyArray_DATA(params_array);
  di_beem=(double*)PyArray_DATA(i_beem_array);

  //Create an array to store the result
  dim=(npy_intp)l;
  res=PyArray_EMPTY(1,&dim,NPY_DOUBLE,0);
  dres=(double*)PyArray_DATA(res);


  double* temp=(double*)PyArray_DATA(bias_array);

  //calcul beem for bell_kaiser_v
  _bell_kaiser_v(l,temp,dres,n ,dparams[0],n_barriers,dparams+1,
          dparams+1+n_barriers);

  //calcul residu
  for(i=0;i<l;i++)
    dres[i]-=di_beem[i];

  //clean PyObjects
  Py_DECREF(bias_array);
  Py_DECREF(i_beem_array);
  Py_DECREF(params_array);

  //return residu
  return PyArray_Return((PyArrayObject*) res);
}



void _bell_kaiser_v(int l ,double * bias, double * i_beem, double n,
        double noise, int n_barriers, double* barrier_height, double* trans_a)
{
  double k;
  int i, j;

  //X*X is faster than pow(X,2)
  if (n==2.0)
  {
    //for each bais
    for (i=0; i<l; i++)
    {
      i_beem[i]=noise;
      //for each barrier heights
      for (j=0;j<n_barriers;j++)
      {
        if(bias[i]<barrier_height[j])
        {
          k=bias[i]-barrier_height[j];
          i_beem[i]+=-trans_a[j]*k*k/bias[i];
        }
      }
    }
  }
  else
  {
    for (i=0; i<l; i++)
    {
      i_beem[i]=noise;

      for (j=0;j<n_barriers;j++)
      {
        if(bias[i]<barrier_height[j])
        {
          i_beem[i]+=-trans_a[j]*pow(fabs(bias[i]-barrier_height[j]),n)/bias[i];
        }
      }
    }

  }
}
