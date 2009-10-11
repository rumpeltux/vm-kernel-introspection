#include <Python.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/types.h>

PyDoc_STRVAR(memory__doc__,        "Arbitrary Memory Access Module");
PyDoc_STRVAR(memory_map__doc__,    "filename, filesize, map_size, map_number -> open filename for access");
PyDoc_STRVAR(memory_set_init_level4_pgt__doc__,    "addr -> set the init_level4_pgt pagetable address");
PyDoc_STRVAR(memory_access__doc__, "type,addr -> read the value at addr");
PyDoc_STRVAR(memory_virt_to_phys__doc__, "virt -> maps kernel virtual address to physical address");
PyDoc_STRVAR(memory_get_defines__doc__, "returns the neccessary kernel defines from the header files as a tuple (PAGE_OFFSET)");

#define MAP_SIZE ((size_t) 1 << 31)
#define PAGE_SIZE ((size_t) 1 << 12)
#define PAGE_ALIGN(x) ((x) & ~0xfff)
#define PAGE_OFFSET(x) ((x) & 0xfff)

int map_fd = -1;
int map_fd1 = -1;
void * memory = NULL;
void * memory1 = NULL;
size_t map_size = 0;
size_t map_size1 = 0;
unsigned long fsize = 0;
unsigned long fsize1 = 0;
off_t map_base = 0;
off_t map_base1 = 0;

typedef unsigned long uint64;

void *memory_access_raw(unsigned long address, int nmap, int *errflag) {
	void* addr;
//	fprintf(stderr, "access: %p\n", (void*)address);
	if(nmap == 0) {
		if(map_fd == -1 || memory == NULL || memory == (void *) -1) {
			*errflag = 1;
			fprintf(stderr, "memory_access: no file yet open (map_fd: %i, memory: %p)\n", map_fd, memory);
			return NULL;
		}

		if(address > fsize) {
			*errflag = 1;
//			fprintf(stderr, "memory_access: address outside file size: fsize: %lu, address: %lu\n", fsize, address);
			fprintf(stderr, "memory_access: address outside file size: fsize: %p, address: %p\n", (void*)fsize, (void*)address);
			return NULL;
		}

		// we are above or below the mapped area
		if(address > (map_base + map_size) || address < map_base) {
			// off_t oldbase = map_base;
			map_base = address - map_size / 2;
			map_base = map_base & ~(sysconf(_SC_PAGE_SIZE) - 1);
			if(memory) {
				if(munmap(memory, map_size) < 0) {
					*errflag = 1;
					fprintf(stderr, "munmap failed\n");
					return NULL;
				}
				memory = NULL;
			}
			memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, map_base);
			if(memory == NULL || memory == MAP_FAILED) {
				*errflag = 1;
				fprintf(stderr, "%s\n", strerror(errno));
				return NULL;
			}
		}

		addr = memory + address - map_base;
		/* if(address == 537851920) {
			fprintf(stderr, "map_base: %i, memory: %i, map_size: %i, address: %i, addr: %i\n", map_base, memory, map_size, address, addr);
		} */
	} else {
		if(map_fd1 == -1 || memory1 == NULL || memory1 == (void *) -1) {
			*errflag = 1;
			fprintf(stderr, "memory_access: no file yet open (map_fd: %i, memory: %p)", map_fd1, memory1);
			return NULL;
		}
		
		if(address > fsize1) {
			*errflag = 1;
			fprintf(stderr, "memory_access: address outside file size: fsize: %lu, address: %lu\n", fsize1, address);
			fprintf(stderr, "memory_access: address outside file size: fsize: %p, address: %p\n", (void*)fsize1, (void*)address);
			return NULL;
		}

		// we are above or below the mapped area
		if(address > (map_base1 + map_size1) || address < map_base1) {
			// off_t oldbase = map_base;
			map_base1 = address - map_size1 / 2;
			map_base1 = map_base1 & ~(sysconf(_SC_PAGE_SIZE) - 1);
			if(memory1) {
				if(munmap(memory1, map_size1) < 0) {
					*errflag = 1;
					fprintf(stderr, "munmap failed\n");
					return NULL;
				}
				memory1 = NULL;
			}
			memory1 = mmap(NULL, map_size1, PROT_READ, MAP_SHARED, map_fd1, map_base1);
			if(memory1 == NULL || memory1 == MAP_FAILED) {
				*errflag = 1;
				fprintf(stderr, "%s\n", strerror(errno));
				return NULL;
			}
		}

		addr = memory1 + address - map_base1;
	}
	return addr;
}

/* #define CONFIG_X86_64
#define __KERNEL__
#define bool void
#define __init  
#define spinlock_t void

#include <asm/page.h>
#include <asm/pgtable.h> */

#include "kernel_defines.h"

// from crashtool x86_64
// ! all defines with fixed addresses only valid vor x86_64
#define MEGABYTES(x)  ((x) * (1048576))
#define ULONG(ADDR)     *((ulong *)((char *)(ADDR)))

#define __START_KERNEL_map  0xffffffff80000000UL
#define MODULES_LEN     (MODULES_END - MODULES_VADDR)

#define VMALLOC_START       0xffffc20000000000UL
#define VMALLOC_END         0xffffe1ffffffffffUL
#define USERSPACE_TOP       0x0000800000000000UL
// #define KERNEL_PAGE_OFFSET  0xffff880000000000UL
#define KERNEL_PAGE_OFFSET_2_6_11         0xffff810000000000UL
#define KERNEL_PAGE_OFFSET_2_6_27         0xffff880000000000UL
#define KERNEL_PAGE_OFFSET __PAGE_OFFSET

#define MODULES_VADDR       0xffffffff88000000UL
#define MODULES_END         0xfffffffffff00000UL

#define VMEMMAP_VADDR       0xffffe20000000000UL
#define VMEMMAP_END         0xffffe2ffffffffffUL

#define IS_KVADDR(addr)	    ((addr) >= KERNEL_PAGE_OFFSET)

#define PML4_SHIFT      39
#define PTRS_PER_PML4   512
#define PGDIR_SHIFT     30
#define PTRS_PER_PGD    512
#define PMD_SHIFT       21
#define PTRS_PER_PMD    512
#define PTRS_PER_PTE    512

// extract offsets from virtual addresses
#define pml4_index(address) (((address) >> PML4_SHIFT) & (PTRS_PER_PML4-1))
#define pgd_index(address)  (((address) >> PGDIR_SHIFT) & (PTRS_PER_PGD-1))
#define pmd_index(address)  (((address) >> PMD_SHIFT) & (PTRS_PER_PMD-1))
#define pte_index(address)  (((address) >> PAGE_SHIFT) & (PTRS_PER_PTE - 1))

#define __PHYSICAL_MASK_SHIFT  40
#define __PHYSICAL_MASK        ((1UL << __PHYSICAL_MASK_SHIFT) - 1)
#define __VIRTUAL_MASK_SHIFT   48
#define __VIRTUAL_MASK         ((1UL << __VIRTUAL_MASK_SHIFT) - 1)
#define PAGE_SHIFT             12
#define KPAGE_SIZE              (1UL << PAGE_SHIFT)
#define PHYSICAL_PAGE_MASK    (~(KPAGE_SIZE-1) & (__PHYSICAL_MASK << PAGE_SHIFT))

#define KERNEL_PAGE_OFFSET_FOR_MASK (KPAGE_SIZE - 1)
#define PAGEMASK	~((unsigned long long)KERNEL_PAGE_OFFSET_FOR_MASK)

#define PAGEBASE(X)           (((unsigned long)(X)) & (unsigned long)PAGEMASK)
#define _2MB_PAGE_MASK       (~((MEGABYTES(2))-1))

#define PAGEOFFSET(X)	((X) & KERNEL_PAGE_OFFSET_FOR_MASK)

// flags
#define _PAGE_PRESENT   0x001
#define _PAGE_PSE       0x080   /* 2MB page */

#define GETPAGE(x) (((x) & ~0x8000000000000fff) + 0xffff880000000000)

unsigned long phys_base = 0;
/* this is the base address for the pml4 page directory
 * it should be the right address on x86_64 otherwise 
 * it can be set using:
 * 
 * pgt = kernel_name('__ksymtab_init_level4_pgt')
 * memory.set_init_level4_pgt(int(pgt.value.get_value()))
 *
 * in your python code
 */
unsigned long init_level4_pgt_start = 0xffffffff80201000;

#define VERBOSEDEBUG 1

/* errflag will be set to 1 on error will be set to 2 if page is not 
 * present
 * for an overview see:
 * http://linux-mm.org/PageTableStructure
 */
unsigned long page_lookup(unsigned long vaddr, int nmap, int* errflag) {
	int myerrflag = 0;
	unsigned long pml4;
	unsigned long pgd_paddr;
	unsigned long pgd;
	unsigned long pmd_paddr;
	unsigned long pmd;

	unsigned long pte_paddr;
	unsigned long pte;

	if(init_level4_pgt_start == 0) {
		fprintf(stderr, "init_level4_pgt not set\n");
		*errflag = 1;
		return 0;
	}

	myerrflag = 0;

	/* first translate the virtual address of the base page
	 * directory to a physical address
	 */
	unsigned long init_level4_pgt_tr = 0;
	if (init_level4_pgt_start >= __START_KERNEL_map) {
		init_level4_pgt_tr = ((init_level4_pgt_start) - (unsigned long)__START_KERNEL_map + phys_base);
	} else if (vaddr >= KERNEL_PAGE_OFFSET) {
		init_level4_pgt_tr = ((init_level4_pgt_start) - KERNEL_PAGE_OFFSET);
	} else {
		init_level4_pgt_tr = init_level4_pgt_start;
	}
	init_level4_pgt_tr = (init_level4_pgt_tr) & PHYSICAL_PAGE_MASK;
	
	/* lookup address for the pgd page directory
	 * the size of one page table entry is sizeof(unsigned long)
	 */
	pml4 = *(unsigned long*)memory_access_raw(init_level4_pgt_tr + PAGEOFFSET(sizeof(unsigned long) * pml4_index(vaddr)), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		fprintf(stderr, "pml4 table address read failed");
		return 0;
	}

	if(!pml4 & _PAGE_PRESENT) {
		// nopage 
		fprintf(stderr, "page not present in pml4\n");
		*errflag = 2;
		return 0;
	}

	pgd_paddr = (pml4) & PHYSICAL_PAGE_MASK;
	
	myerrflag = 0;
#ifdef VERBOSEDEBUG
	fprintf(stderr, "fsize: %p pgd_paddr: %p\n", (void*)fsize, (void*)pgd_paddr);
	fprintf(stderr, "pgd_index: %lu, pgd_paddr_ind: %p\n", pgd_index(vaddr), (void*)(pgd_paddr + sizeof(unsigned long) * pgd_index(vaddr)));
#endif
	/* lookup address for the pgd page directory */	
	pgd = *(unsigned long*)memory_access_raw(pgd_paddr + PAGEOFFSET(sizeof(unsigned long) * pgd_index(vaddr)), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		fprintf(stderr, "pgd table address read failed");
		return 0;
	}

	if(!(pgd & _PAGE_PRESENT)) {
		*errflag = 2;
		fprintf(stderr, "page not present in pgd\n");
		return 0;
	}

	pmd_paddr = pgd & PHYSICAL_PAGE_MASK;
	myerrflag = 0;

#ifdef VERBOSEDEBUG
	fprintf(stderr, "fsize: %p, pmd_paddr: %p\n", (void*)fsize, (void*)pmd_paddr);
#endif

#ifdef VERBOSEDEBUG
	fprintf(stderr, "pmd_index: %lu, pmd_paddr_ind: %p\n", pmd_index(vaddr), (void*)(pmd_paddr + sizeof(unsigned long) * pmd_index(vaddr)));
#endif
	/* lookup address for the pmd page directory */
	pmd = *(unsigned long*)memory_access_raw(pmd_paddr + PAGEOFFSET(sizeof(unsigned long) * pmd_index(vaddr)), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		fprintf(stderr, "pmd table address read failed");
		return 0;
	}
	if(!(pmd & _PAGE_PRESENT)) {
		*errflag = 2;
		fprintf(stderr, "page not present in pgd\n");
		return 0;
	}

	if(pmd & _PAGE_PSE) {
		/* 2MB Page */
		unsigned long physaddr = (pmd & PHYSICAL_PAGE_MASK) + (vaddr & ~_2MB_PAGE_MASK);
		return physaddr;
	}

	pte_paddr = pmd & PHYSICAL_PAGE_MASK;

#ifdef VERBOSEDEBUG
	fprintf(stderr, "fsize: %p, pte_paddr: %p\n", (void*)fsize, (void*)pte_paddr);
	fprintf(stderr, "pte_index: %lu, pte_paddr_ind: %p\n", pte_index(vaddr), (void*)(pte_paddr + sizeof(unsigned long) * pte_index(vaddr)));
#endif
	
	/* lookup the final page table entry */
	pte = *(unsigned long*)memory_access_raw(pte_paddr + PAGEOFFSET(sizeof(unsigned long) * pte_index(vaddr)), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		fprintf(stderr, "pmd table address read failed");
		return 0;
	}
	if(!(pte & (_PAGE_PRESENT))) {
		*errflag = 2;
		fprintf(stderr, "page not present in pte\n");
		return 0;
	}

#ifdef VERBOSEDEBUG
	fprintf(stderr, "page_offset: %p\n", (void*) (((unsigned long)(vaddr)) & KERNEL_PAGE_OFFSET_FOR_MASK));
#endif
	unsigned long physaddr = (pte & PHYSICAL_PAGE_MASK) + (((unsigned long)(vaddr)) & KERNEL_PAGE_OFFSET_FOR_MASK);

	return physaddr;
}

unsigned long map_kernel_virtual_to_physical(unsigned long virtual, int nmap, int* errflag) {
	/* first check, if we have a kernel virtual address here
	 * since userspace address mapping is not supported
	 */
        if(IS_KVADDR(virtual)) {
		unsigned long physaddr = 0;
		/* if we can do the job with a simple linear translation 
		 * subtract the adequate constant from the virtual address
		 */
		if(!((virtual >= VMALLOC_START && virtual <= VMALLOC_END) ||
	   	     (virtual >= VMEMMAP_VADDR && virtual <= VMEMMAP_END) ||
	             (virtual >= MODULES_VADDR && virtual <= MODULES_END))) { 
			if (virtual >= (unsigned long)__START_KERNEL_map) {
				*errflag = 0;
				physaddr = ((virtual) - (unsigned long)__START_KERNEL_map + phys_base);
#ifdef VERBOSEDEBUG
				fprintf(stderr, "start_kern_tr: %p -> %p\n", (void*)virtual, (void*)physaddr);
#endif
			} else /* if(virtual >= (unsigned long)KERNEL_PAGE_OFFSET) */ {
				*errflag = 0;
				physaddr = ((virtual) - KERNEL_PAGE_OFFSET);
#ifdef VERBOSEDEBUG
				fprintf(stderr, "pg_offs_tr: %p -> %p\n", (void*)virtual, (void*)physaddr);
#endif
			}
		} else {
			// otherwise use the address_lookup function
			physaddr = page_lookup(virtual, nmap, errflag);
#ifdef VERBOSEDEBUG
			fprintf(stderr, "kpage: %p -> %p\n", (void*)virtual, (void*)physaddr);
#endif

		}
		return physaddr;
	}
	fprintf(stderr, "not a kernel virtual address: %p\n", (void*)virtual);
	*errflag = 1;
	return 0;
}

static PyObject * py_memory_virt_to_phys(PyObject *self, PyObject *args)
{
	unsigned long virt;
	unsigned long phys;
	int nmap = 0;
	int errflag = 0;

	if(!PyArg_ParseTuple(args, "ki", &virt, &nmap))
		return NULL;
	
	phys = map_kernel_virtual_to_physical(virt, nmap, &errflag);
	if(errflag == 2) {
		// PyObject * exp = PyErr_NewException("cexcp.PageNotPresent", NULL, NULL);
		PyErr_Format(PyExc_ValueError, "page for address %p not present", (void*)virt);
		return NULL;
	} else if(errflag != 0) {
		PyErr_SetString(PyExc_RuntimeError, "error mapping virtual address");
		return NULL;
	}
	return Py_BuildValue("k", phys);
}

static PyObject * py_memory_map(PyObject *self, PyObject *args)
{
    char * filename;
    int nmap = 0;
    long mymap_size = 0;
    unsigned long tempfsize = 0;

    if (!PyArg_ParseTuple(args, "skki", &filename, &tempfsize, &mymap_size, &nmap))
        return NULL;

    FILE* sfd = fopen(filename, "r");
    if(sfd == NULL) {
	    PyErr_SetString(PyExc_IOError, strerror(errno));
	    return NULL;
    }
//     fseek(sfd, 0, SEEK_END);
//     tempfsize = ftell(sfd);
// //    fprintf(stderr, "%s: %li\n", filename, tempfsize);
//     fseek(sfd, 0, SEEK_SET);
//     fclose(sfd);

    if(nmap == 0) { 
	    map_size = mymap_size;
	    fsize = tempfsize;
	    if(map_fd != -1) { /* there is already another mapping. clear it first */
		    if(memory) {
			    munmap(memory, PAGE_SIZE);
			    memory = NULL;
		    }
		    close(map_fd);
	    }
	    map_fd = open(filename, O_RDONLY, 0);
	    if(map_fd == -1) {
		    PyErr_SetString(PyExc_IOError, strerror(errno));
		    return NULL;
	    }    
	    memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, map_base);
	    if(memory == NULL || memory == (void *) -1) {
		    PyErr_SetString(PyExc_RuntimeError, strerror(errno));
		    return NULL;
	    } 
    } else {
	    map_size1 = mymap_size;
	    fsize1 = tempfsize;
	    if(map_fd1 != -1) { /* there is already another mapping. clear it first */
		    if(memory1) {
			    munmap(memory1, PAGE_SIZE);
			    memory1 = NULL;
		    }
		    close(map_fd1);
	    }
	    map_fd1 = open(filename, O_RDONLY, 0);
	    if(map_fd1 == -1) {
		    PyErr_SetString(PyExc_IOError, strerror(errno));
		    //return Py_BuildValue("s", strerror(errno));
		    return NULL;
	    }    
	    memory1 = mmap(NULL, map_size1, PROT_READ, MAP_SHARED, map_fd1, map_base1);
	    if(memory1 == NULL || memory1 == (void *) -1) {
		    PyErr_SetString(PyExc_RuntimeError, strerror(errno));
		    return NULL;
		    //      return Py_BuildValue("s", strerror(errno));
	    }
    }
    
    return Py_BuildValue(""); // None == Success
}

static PyObject *py_memory_set_init_level4_pgt(PyObject *self, PyObject *args) {
	if(!PyArg_ParseTuple(args, "k", &init_level4_pgt_start))
		return NULL;
	return Py_BuildValue("");
}

static PyObject * py_memory_access(PyObject *self, PyObject *args)
{
    char type;
    unsigned long address;
    void * addr;
    int nmap = 0;

    if (!PyArg_ParseTuple(args, "bki", &type, &address, &nmap))
        return NULL;

    int errflag = 0;
    addr = memory_access_raw(address, nmap, &errflag);
    if(errflag != 0) {
	    PyErr_Format(PyExc_RuntimeError, "error accessing memory at %p", (void*)address);
	    return NULL;
    }

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

static PyObject * py_memory_get_defines(PyObject *self, PyObject *args) {
	return Py_BuildValue("(k)", KERNEL_PAGE_OFFSET);
}

static PyMethodDef memory_methods[] = {
	{"map",     py_memory_map,    METH_VARARGS, memory_map__doc__},
	{"set_init_level4_pgt",     py_memory_set_init_level4_pgt,    METH_VARARGS, memory_set_init_level4_pgt__doc__},
	{"access",  py_memory_access, METH_VARARGS, memory_access__doc__},
	{"virt_to_phys", py_memory_virt_to_phys, METH_VARARGS, memory_virt_to_phys__doc__},
	{"get_defines", py_memory_get_defines, METH_VARARGS, memory_get_defines__doc__},
	{NULL, NULL}      /* sentinel */
};

PyMODINIT_FUNC
initmemory(void)
{
	// PyObject* mod = Py_InitModule3("memory", memory_methods, memory__doc__);
	Py_InitModule3("memory", memory_methods, memory__doc__);
	// PyModule_AddObject(mod, "PageNotPresent", PyErr_NewException("memory.PageNotPresent", NULL, NULL));
}
