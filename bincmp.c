#include <Python.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/types.h>

PyDoc_STRVAR(bincmp__doc__,        "Binary Memory Dump Comparision");
PyDoc_STRVAR(bincmp_cmp__doc__,    "filename, filename -> compare the two files and return differing regions");

static PyObject * py_bincmp_cmp(PyObject *self, PyObject *args)
{
    char *filename1;
    char *filename2;

    if (!PyArg_ParseTuple(args, "ss", &filename1, &filename2))
        return NULL;
    
    FILE* f1;
    FILE* f2;

    f1 = fopen(filename1, "r");
    if(f1 == NULL) {
	    return Py_BuildValue("s", "could not open file1");
    }
    f2 = fopen(filename2, "r");
    if(f2 == NULL) {
	    fclose(f1);
	    return Py_BuildValue("s", "could not open file2");
    }

    long flen1 = 0;
    long flen2 = 0;

    fseek(f1, 0, SEEK_END);
    flen1 = ftell(f1);
    fseek(f1, 0, SEEK_SET);
    fseek(f2, 0, SEEK_END);
    flen2 = ftell(f2);
    fseek(f2, 0, SEEK_SET);

    if(flen1 != flen2) {
	    PyObject* pylist = PyList_New(0);
	    PyObject* pyentry = PyTuple_New(2);
	    PyObject* first = PyInt_FromLong(0);
	    PyObject* second = PyInt_FromLong(flen1);
	    PyTuple_SetItem(first, 0, pyentry);
	    PyTuple_SetItem(second, 1, pyentry);
	    PyList_Append(pylist, pyentry);
	    fclose(f1);
	    fclose(f2);
	    return pylist;
    }

    char b1, b2;
    long s, e;
    s = e = 0;
    int inside = 0;
    PyObject* pylist = PyList_New(0);
    while(fread(&b1, sizeof(char), 1, f1) == sizeof(char) && fread(&b2, sizeof(char), 1, f2) == sizeof(char)) {
	if(b1 != b2) {
		if(inside == 0) {
			s = ftell(f1);
			e = ftell(f1);
			inside = 1;
		} else {
			e = ftell(f1);
		}
	} else {
		if(inside == 1) {
			PyObject* pyentry = PyTuple_New(2);
			PyObject* first = PyInt_FromLong(s);
			PyObject* second = PyInt_FromLong(e);
	    		PyTuple_SetItem(first, 0, pyentry);
	    		PyTuple_SetItem(second, 1, pyentry);
			PyList_Append(pylist, pyentry);
			inside = 0;
		}
	}
    }

    fclose(f1);
    fclose(f2);

    return pylist; 
}

static PyMethodDef bincmp_methods[] = {
	{"cmp",     py_bincmp_cmp,    METH_VARARGS, bincmp_cmp__doc__},
	{NULL, NULL}      /* sentinel */
};

PyMODINIT_FUNC
initbincmp(void)
{
	Py_InitModule3("bincmp", bincmp_methods, bincmp__doc__);
}
