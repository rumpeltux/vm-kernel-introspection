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
off_t map_base = 0;
typedef uint64 unsigned long;

#define PAGE_SHIFT 12
#define PTE_BITS 9
#define PTE_SHIFT (PAGE_SHIFT+PTE_BITS)
#define PMD_BITS 9
#define PMD_SHIFT (PTE_SHIFT+PMD_BITS)
#ifndef PAE
#define PUD_BITS 9
#define PUD_SHIFT (PMD_SHIFT+PUD_BITS)
#define PGDIR_BITS 7
#define PGDIR_SHIFT (PUD_SHIFT+PGDIR_BITS)
#else
#define PGDIR_BITS 2
#define PGDIR_SHIFT (PMD_SHIFT+PGDIR_BITS)
#endif


void * address_lookup(void * p, uint64 * pgdir) {
    /* TODO: Fehlerbehandlung, Flags prüfen (present etc) */
    uint64 pgd_offset = ((uint64 p) >> (PGDIR_SHIFT-PAGE_SHIFT)) & ((1 << PGDIR_BITS)-1);
    #ifndef PAE
      uint64 pud_offset = ((uint64 p) >> (PUD_SHIFT  -PAGE_SHIFT)) & ((1 << PUD_BITS)-1);
    #endif
    uint64 pmd_offset = ((uint64 p) >> (PMD_SHIFT  -PAGE_SHIFT)) & ((1 << PMD_BITS)-1);
    uint64 pte_offset = ((uint64 p) >> (PTE_SHIFT  -PAGE_SHIFT)) & ((1 << PTE_BITS)-1);
    #ifndef PAE
      uint64 * pud = pgd[pgd_offset] & ~(PAGE_SIZE-1);
      printf("  pgt[%ld]: %p\n", pgd_offset, pud);
      uint64 * pmd = pud[pud_offset] & ~(PAGE_SIZE-1);
      printf("   pud[%ld]: %p\n", pud_offset, pmd);
    #else
      uint64 * pmd = pgd[pgd_offset] & ~(PAGE_SIZE-1);
    #endif
    uint64 * pte = pmd[pme_offset] & ~(PAGE_SIZE-1);
    printf("    pmd[%ld]: %p\n", pmd_offset, pte);
    void * page  = pte[pte_offset] & ~(PAGE_SIZE-1);
    printf("     pte[%ld]: %p\n", pte_offset, page);
    return page;
}

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
    
    memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, map_base);
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
    
    if(map_fd == -1 || memory == NULL || memory == (void *) -1)
        return Py_BuildValue("s", "no file yet open"); // not yet mapped
    
    // we are above or below the mapped area
    if(address > (map_base + map_size) || address < map_base) {
	    off_t oldbase = map_base;
	    map_base = address - map_size / 2;
	    map_base = map_base & ~(sysconf(_SC_PAGE_SIZE) - 1);
	    printf("remapping from base 0x%x to base 0x%x\n", (unsigned int)oldbase, (unsigned int)map_base);
	    if(memory) {
		    munmap(memory, PAGE_SIZE);
		    memory = NULL;
	    }
	    memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, map_base);
	    if(memory == NULL || memory == MAP_FAILED)
		    return Py_BuildValue("s", strerror(errno));
    }
        // return Py_BuildValue("s", "out of area"); // out of area

    addr = memory + address - map_base;
    
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
