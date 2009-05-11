#include <Python.h>

PyDoc_STRVAR(memory__doc__,        "Arbitrary Memory Access Module");
PyDoc_STRVAR(memory_map__doc__,    "map the target memory");
PyDoc_STRVAR(memory_access__doc__, "type,addr -> read the value at addr");

static PyObject * py_memory_map(PyObject *self, PyObject *args)
{
    const char *command;
    //int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    //sts = map(command);
    return Py_BuildValue("s", command);
}

static PyObject * py_memory_access(PyObject *self, PyObject *args)
{
    char type;
    void * addr;

    if (!PyArg_ParseTuple(args, "bk", &type, (unsigned long long) &addr))
        return NULL;
    
    printf("accessing %d at %p\n", type, addr);
    /* TODO do mapping and stuff */
    switch(type) {
    case 0:  return Py_BuildValue("B", *(unsigned char   *)addr);
    case 1:  return Py_BuildValue("b", *(         char   *)addr);
    case 2:  return Py_BuildValue("H", *(unsigned short  *)addr);
    case 3:  return Py_BuildValue("h", *(         short  *)addr);
    case 4:  return Py_BuildValue("I", *(unsigned int    *)addr);
    case 5:  return Py_BuildValue("i", *(         int    *)addr);
    case 6:  return Py_BuildValue("k", *(unsigned long   *)addr);
    case 7:  return Py_BuildValue("l", *(         long   *)addr);
    case 8:  return Py_BuildValue("d", *(         double *)addr);
    case 9:  return Py_BuildValue("f", *(         float  *)addr);
    case 10: return Py_BuildValue("s",  (         char   *)addr);
    }
    return Py_BuildValue(""); //None
}


static PyMethodDef memory_methods[] = {
	{"map",     py_memory_map,    METH_VARARGS, memory_map__doc__},
	{"access",  py_memory_access, METH_VARARGS, memory_access__doc__},
	{NULL, NULL}      /* sentinel */
};

PyMODINIT_FUNC
initmemory(void)
{
	Py_InitModule3("memory", memory_methods, memory__doc__);
}



