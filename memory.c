#include <Python.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/types.h>

PyDoc_STRVAR(memory__doc__,        "Arbitrary Memory Access Module");
PyDoc_STRVAR(memory_map__doc__,    "filename -> open filename for access");
PyDoc_STRVAR(memory_access__doc__, "type,addr -> read the value at addr");

#define MAP_SIZE ((size_t) 1 << 31)
#define PAGE_SIZE ((size_t) 1 << 12)
#define PAGE_ALIGN(x) ((x) & ~0xfff)
#define PAGE_OFFSET(x) ((x) & 0xfff)
int map_fd = -1;
void * memory = NULL;
size_t map_size = 0;

static PyObject * py_memory_map(PyObject *self, PyObject *args)
{
    char * filename;

    if (!PyArg_ParseTuple(args, "sk", &filename, &map_size))
        return NULL;
    
    if(map_fd != -1) { /* there is already another mapping. clear it first */
      if(memory) {
	munmap(memory, PAGE_SIZE);
	memory = NULL;
      }
      close(map_fd);
    }
    map_fd = open(filename, O_RDONLY, 0);
    if(map_fd == -1)
        return Py_BuildValue("s", strerror(errno));
    
    memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, 0);
    if(memory == NULL || memory == (void *) -1)
      return Py_BuildValue("s", strerror(errno));
    
    return Py_BuildValue(""); // None == Success
}

static PyObject * py_memory_access(PyObject *self, PyObject *args)
{
    char type;
    unsigned long long address;
    void * addr;
    char buf[1024];

    if (!PyArg_ParseTuple(args, "bk", &type, &address))
        return NULL;
    
    if(map_fd == -1 || memord == NULL || memory == (void *) -1)
        return Py_BuildValue("s", "no file yet open"); // not yet mapped

    if(address > map_size)
        return Py_BuildValue("s", "out of area"); // out of area

    addr = memory + address;
    
    printf("accessing %d at %p (is %p)\n", type, addr, (void *) (address));
       
//     {
//         printf("new pos: %lx\n", lseek(map_fd, address, SEEK_SET));
// 	if(read(map_fd, buf, 1024) == -1) return Py_BuildValue("s", strerror(errno));
// 	addr = buf;
//     }
// 	
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