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

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
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

#else

PyMODINIT_FUNC init_pure_c(void)
{
  PyObject *m = Py_InitModule3("_pure_c", module_methods, module_docstring);
  if (m==NULL)
    return;
  import_array()
}
#endif

static PyObject *bell_kaiser_v(PyObject *self, PyObject *args)
{
  PyObject *bias, *i_beem, *params;
  PyArrayObject *bias_array, *params_array;
  double *dparams, n;
  unsigned int l, n_barriers;

  //Extract argument
  if (!PyArg_ParseTuple(args, "OdO", &bias, &n, &params)) return NULL;
  bias_array = (PyArrayObject*) PyArray_FROM_OTF(bias, NPY_DOUBLE, NPY_ARRAY_CARRAY_RO);
  params_array = (PyArrayObject*) PyArray_FROM_OTF(params, NPY_DOUBLE, NPY_ARRAY_CARRAY_RO);


  //Retrieve dimension of bias and number of barrier height
  n_barriers=((int)PyArray_SIZE(params_array)-1)/2;
  l=(int)PyArray_SIZE(bias_array);
  dparams=(double*)PyArray_DATA(params_array);

  //Create an array to store the result
  i_beem=PyArray_EMPTY(PyArray_NDIM(bias_array),PyArray_SHAPE(bias_array),NPY_DOUBLE,0);

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
  PyObject *bias, *i_beem, *res, *params;
  PyArrayObject *i_beem_array, *bias_array, *params_array;
  double *dparams, n, *di_beem, *dres;
  int l, i, n_barriers;

  //Extract parameters
  if (!PyArg_ParseTuple(args, "OOOd",&params, &bias, &i_beem, &n)) return NULL;
  bias_array = (PyArrayObject*)PyArray_FROM_OTF(bias, NPY_DOUBLE, NPY_ARRAY_CARRAY_RO);
  i_beem_array = (PyArrayObject*)PyArray_FROM_OTF(i_beem, NPY_DOUBLE, NPY_ARRAY_CARRAY_RO);
  params_array = (PyArrayObject*)PyArray_FROM_OTF(params, NPY_DOUBLE, NPY_ARRAY_CARRAY_RO);

  //Get Data
  l=(int)PyArray_SIZE(bias_array);
  n_barriers=((int)PyArray_DIM(params_array, 0)-1)/2;
  dparams=(double*)PyArray_DATA(params_array);
  di_beem=(double*)PyArray_DATA(i_beem_array);

  //Create an array to store the result
  res=PyArray_EMPTY(PyArray_NDIM(bias_array),PyArray_SHAPE(bias_array),NPY_DOUBLE,0);
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
