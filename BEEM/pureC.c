#include <Python.h>
#include <numpy/arrayobject.h>


static char module_docstring[] ="This module provides an interface for calculating chi-squared using C.";

static char bell_kaiser_v_docstring[] = "Calculate the chi-squared of some data given a model.";

static PyObject *bell_kaiser_v(PyObject *self, PyObject *args);

static PyMethodDef module_methods[] = {
  {"bell_kaiser_v",bell_kaiser_v, METH_VARARGS,bell_kaiser_v_docstring},
  {NULL,NULL,0,NULL}
};

PyMODINIT_FUNC init_pureC(void)
{
  PyObject *m = Py_InitModule3("_pureC", module_methods, module_docstring);
  if (m==NULL)
    return;
  import_array();
}

static PyObject *bell_kaiser_v(PyObject *self, PyObject *args)
{
  PyObject *bias_obj, *i_beem, *bias_array;
  double *biasc, *i_beemc, barrier_height, trans_a, noise, k;
  unsigned int l,i;
  int dims []={0};

  if (!PyArg_ParseTuple(args, "Oddd", &bias_obj, &barrier_height, &trans_a, &noise)) return NULL;
  
  bias_array = PyArray_FROM_OTF(bias_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  l=(int)PyArray_DIM(bias_array, 0);
  dims[0]=l;
  i_beem=PyArray_EMPTY(1,(npy_intp*)dims,NPY_DOUBLE,0);

  biasc=(double*)PyArray_DATA(bias_array);
  i_beemc=(double*)PyArray_DATA(i_beem);

  for (i=0; i<l; i++)
  {
    if(biasc[i]>barrier_height)
        i_beemc[i]=noise;
    else{
      k=biasc[i]-barrier_height;
      i_beemc[i]=-trans_a*k*k/biasc[i]+noise;
    }
  }

  Py_DECREF(bias_array);

  return PyArray_Return((PyArrayObject*) i_beem);
}
