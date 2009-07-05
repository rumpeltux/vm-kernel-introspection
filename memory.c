#include <Python.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/types.h>

PyDoc_STRVAR(memory__doc__,        "Arbitrary Memory Access Module");
PyDoc_STRVAR(memory_map__doc__,    "filename -> open filename for access");
PyDoc_STRVAR(memory_set_init_level4_pgt__doc__,    "addr -> set the init_level4_pgt pagetable address");
PyDoc_STRVAR(memory_access__doc__, "type,addr -> read the value at addr");
PyDoc_STRVAR(memory_virt_to_phys__doc__, "virt -> maps kernel virtual address to physical address");

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

// #define PAGE_SHIFT 12
// #define PTE_BITS 9
// #define PTE_SHIFT (PAGE_SHIFT+PTE_BITS)
// #define PMD_BITS 9
// #define PMD_SHIFT (PTE_SHIFT+PMD_BITS)
// #ifndef PAE
//   #define PUD_BITS 9
//   #define PUD_SHIFT (PMD_SHIFT+PUD_BITS)
//   #define PGDIR_BITS 7
//   #define PGDIR_SHIFT (PUD_SHIFT+PGDIR_BITS)
// #else
//   #define PGDIR_BITS 2
//   #define PGDIR_SHIFT (PMD_SHIFT+PGDIR_BITS)
// #endif
// 
// void * address_lookup(void * p, uint64 * pgd) {
//     /* TODO: Fehlerbehandlung, Flags prüfen (present etc) */
//     uint64 pgd_offset = (((uint64) p) >> (PGDIR_SHIFT-PAGE_SHIFT)) & ((1 << PGDIR_BITS)-1);
//     #ifndef PAE
//       uint64 pud_offset = (((uint64) p) >> (PUD_SHIFT  -PAGE_SHIFT)) & ((1 << PUD_BITS)-1);
//     #endif
//     uint64 pmd_offset = (((uint64) p) >> (PMD_SHIFT  -PAGE_SHIFT)) & ((1 << PMD_BITS)-1);
//     uint64 pte_offset = (((uint64) p) >> (PTE_SHIFT  -PAGE_SHIFT)) & ((1 << PTE_BITS)-1);
//     #ifndef PAE
//       uint64 * pud = pgd[pgd_offset] & ~(PAGE_SIZE-1);
//       printf("  pgt[%ld]: %p\n", pgd_offset, pud);
//       uint64 * pmd = pud[pud_offset] & ~(PAGE_SIZE-1);
//       printf("   pud[%ld]: %p\n", pud_offset, pmd);
//     #else
//       uint64 * pmd = pgd[pgd_offset] & ~(PAGE_SIZE-1);
//     #endif
//     uint64 * pte = pmd[pmd_offset] & ~(PAGE_SIZE-1);
//     printf("    pmd[%ld]: %p\n", pmd_offset, pte);
//     void * page  = pte[pte_offset] & ~(PAGE_SIZE-1);
//     printf("     pte[%ld]: %p\n", pte_offset, page);
//     return page;
// }

void *memory_access_raw(unsigned long address, int nmap, int *errflag) {
	void* addr;
	if(nmap == 0) {
		if(map_fd == -1 || memory == NULL || memory == (void *) -1) {
			*errflag = 1;
			printf("memory_access: no file yet open (map_fd: %i, memory: %p)\n", map_fd, memory);
			return NULL;
		}

		if(address > fsize) {
			*errflag = 1;
			printf("memory_access: address outside file size: fsize: %li, address: %li\n", fsize, address);
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
					printf("munmap failed\n");
					return NULL;
				}
				memory = NULL;
			}
			memory = mmap(NULL, map_size, PROT_READ, MAP_SHARED, map_fd, map_base);
			if(memory == NULL || memory == MAP_FAILED) {
				*errflag = 1;
				printf("%s\n", strerror(errno));
				return NULL;
			}
		}

		addr = memory + address - map_base;
		/* if(address == 537851920) {
			printf("map_base: %i, memory: %i, map_size: %i, address: %i, addr: %i\n", map_base, memory, map_size, address, addr);
		} */
	} else {
		if(map_fd1 == -1 || memory1 == NULL || memory1 == (void *) -1) {
			*errflag = 1;
			printf("memory_access: no file yet open (map_fd: %i, memory: %p)", map_fd1, memory1);
			return NULL;
		}
		
		if(address > fsize1) {
			*errflag = 1;
			printf("memory_access: address outside file size: fsize: %li, address: %li\n", fsize1, address);
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
					printf("munmap failed\n");
					return NULL;
				}
				memory1 = NULL;
			}
			memory1 = mmap(NULL, map_size1, PROT_READ, MAP_SHARED, map_fd1, map_base1);
			if(memory1 == NULL || memory1 == MAP_FAILED) {
				*errflag = 1;
				printf("%s\n", strerror(errno));
				return NULL;
			}
		}

		addr = memory1 + address - map_base1;
	}
	return addr;
}

// from crashtool x86_64
#define MEGABYTES(x)  ((x) * (1048576))
#define ULONG(ADDR)     *((ulong *)((char *)(ADDR)))
#define ULONGLONG(ADDR) *((ulonglong *)((char *)(ADDR)))
#define ULONG_PTR(ADDR) *((ulong **)((char *)(ADDR)))

#define __START_KERNEL_map  0xffffffff80000000UL
#define MODULES_LEN     (MODULES_END - MODULES_VADDR)

#define VMALLOC_START       0xffffc20000000000
#define VMALLOC_END         0xffffe1ffffffffff
#define USERSPACE_TOP       0x0000800000000000
#define KERNEL_PAGE_OFFSET  0xffff880000000000
#define MODULES_VADDR       0xffffffff88000000
#define MODULES_END         0xfffffffffff00000

#define VMEMMAP_VADDR       0xffffe20000000000
#define VMEMMAP_END         0xffffe2ffffffffff

#define IS_KVADDR(addr)	    ((addr) >= KERNEL_PAGE_OFFSET)

#define PML4_SHIFT      39
#define PTRS_PER_PML4   512
#define PGDIR_SHIFT     30
#define PTRS_PER_PGD    512
#define PMD_SHIFT       21
#define PTRS_PER_PMD    512
#define PTRS_PER_PTE    512

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

#define PAGEMASK	~((unsigned long long)KERNEL_PAGE_OFFSET)

#define PAGEBASE(X)           (((unsigned long)(X)) & (unsigned long)PAGEMASK)
#define _2MB_PAGE_MASK       (~((MEGABYTES(2))-1))

#define _PAGE_PRESENT   0x001
#define _PAGE_PSE       0x080   /* 2MB page */

unsigned long phys_base = 0;
unsigned long init_level4_pgt = 0xffffffff80201000;

/*
 *  x86_64 __pa() clone.
 */
unsigned long x86_64_VTOP(unsigned long vaddr)
{
        if (vaddr >= __START_KERNEL_map)
                return ((vaddr) - (unsigned long)__START_KERNEL_map + phys_base);
        else
                return ((vaddr) - KERNEL_PAGE_OFFSET);
}

int
IS_VMALLOC_ADDR(unsigned long vaddr)
{
        return ((vaddr >= VMALLOC_START && vaddr <= VMALLOC_END) ||
                 (vaddr >= VMEMMAP_VADDR && vaddr <= VMEMMAP_END) ||
                (vaddr >= MODULES_VADDR && vaddr <= MODULES_END) ||
		(vaddr >= __START_KERNEL_map) || 
		(vaddr >= KERNEL_PAGE_OFFSET));
}

unsigned long page_lookup(unsigned long vaddr, int nmap, int* errflag) {
	int myerrflag = 0;
	unsigned long pml4;
	unsigned long pgd_paddr;
	unsigned long pgd;
	unsigned long mpgd;
	unsigned long pgd_pte;
	unsigned long pmd_paddr;
	unsigned long pmd;
	unsigned long mpmd;
	unsigned long pmd_pte;

	unsigned long pte_paddr;
	unsigned long ptep;
	unsigned long mpte;
	unsigned long pte;

	if(init_level4_pgt == 0) {
		printf("init_level4_pgt not set\n");
		*errflag = 1;
		return 0;
	}

	//pml4 = (init_level4_pgt) + pml4_index(vaddr);
	myerrflag = 0;
	pml4 = *(unsigned long*)memory_access_raw(init_level4_pgt + pml4_index(vaddr), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		printf("pml4 table address read failed");
		return 0;
	}

	if(!(pml4) & _PAGE_PRESENT) {
		// nopage 
		printf("page not present\n");
		*errflag = 1;
		return 0;
	}

	pgd_paddr = (pml4) & PHYSICAL_PAGE_MASK;
	myerrflag = 0;
	mpgd = *(unsigned long*)memory_access_raw(pgd_paddr, nmap, &myerrflag);
	// pgd = ((unsigned long*)pgd_paddr) + pgd_index(vaddr);
	pgd = *(unsigned long*)memory_access_raw(pgd_paddr + pgd_index(vaddr), nmap, &myerrflag);
	if(myerrflag != 0) {
		*errflag = 1;
		printf("pgd table address read failed");
		return 0;
	}
	pgd_pte = ULONG(mpgd + (((unsigned long)(pgd)) & KERNEL_PAGE_OFFSET));
	if(!(pgd_pte & _PAGE_PRESENT)) {
		*errflag = 1;
		printf("page not present in pgd\n");
		return 0;
	}

	pmd_paddr = pgd_pte & PHYSICAL_PAGE_MASK;
	myerrflag = 0;
	mpmd = *(unsigned long*)memory_access_raw(pmd_paddr, nmap, &myerrflag);
	pmd = *(unsigned long*)memory_access_raw(pmd_paddr + pmd_index(vaddr), nmap, &myerrflag);
	// pmd = ((unsigned long*)pmd_paddr) + pmd_index(vaddr);
	if(myerrflag != 0) {
		*errflag = 1;
		printf("pmd table address read failed");
		return 0;
	}
	pmd_pte = ULONG(mpmd + (((unsigned long)(pmd)) & KERNEL_PAGE_OFFSET));
	if(!(pmd_pte & _PAGE_PRESENT)) {
		*errflag = 1;
		printf("page not present in pgd\n");
		return 0;
	}
	if(pmd_pte & _PAGE_PSE) {
		/* 2MB Page */
		unsigned long physpage = (PAGEBASE(pmd_pte) & PHYSICAL_PAGE_MASK) + (vaddr & ~_2MB_PAGE_MASK);
		unsigned long physaddr = physpage & PHYSICAL_PAGE_MASK;
		return physaddr;
	}

	pte_paddr = pmd_pte & PHYSICAL_PAGE_MASK;
	mpte = *(unsigned long*)memory_access_raw(pte_paddr, nmap, &myerrflag);
	ptep = *(unsigned long*)memory_access_raw(pte_paddr + pte_index(vaddr), nmap, &myerrflag);
	//ptep = ((unsigned long*)pte_paddr) + pte_index(vaddr);
	if(myerrflag != 0) {
		*errflag = 1;
		printf("pmd table address read failed");
		return 0;
	}
	pte = ULONG(mpte + (((unsigned long)(ptep)) & KERNEL_PAGE_OFFSET));
	if(!(pte & (_PAGE_PRESENT))) {
		*errflag = 1;
		printf("page not present in pte\n");
		return 0;
	}

	unsigned long physpage = (PAGEBASE(pte) & PHYSICAL_PAGE_MASK) + (((unsigned long)(vaddr)) & KERNEL_PAGE_OFFSET);

	unsigned long physaddr = physpage & PHYSICAL_PAGE_MASK;
	return physaddr;
}

unsigned long map_kernel_virtual_to_physical(unsigned long virtual, int nmap, int* errflag) {
        if(IS_KVADDR(virtual)) {
                if(!IS_VMALLOC_ADDR(virtual)) {
			*errflag = 0;
                        return x86_64_VTOP(virtual);
                } else {
			// use the address_lookup function
			return page_lookup(virtual, nmap, errflag);
		}
        }
	printf("not a virtual address\n");
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
	if(errflag != 0) {
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

    if (!PyArg_ParseTuple(args, "ski", &filename, &mymap_size, &nmap))
        return NULL;

    FILE* sfd = fopen(filename, "r");
    if(sfd == NULL) {
	    PyErr_SetString(PyExc_IOError, strerror(errno));
	    return NULL;
    }
    fseek(sfd, 0, SEEK_END);
    tempfsize = ftell(sfd);
//    printf("%s: %li\n", filename, tempfsize);
    fseek(sfd, 0, SEEK_SET);
    fclose(sfd);

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
	if(!PyArg_ParseTuple(args, "k", &init_level4_pgt))
		return NULL;
	return Py_BuildValue("");
}

static PyObject * py_memory_access(PyObject *self, PyObject *args)
{
    char type;
    unsigned long long address;
    void * addr;
    int nmap = 0;
    //char buf[1024];

    if (!PyArg_ParseTuple(args, "bki", &type, &address, &nmap))
        return NULL;

    int errflag = 0;
    addr = memory_access_raw(address, nmap, &errflag);
    if(errflag != 0) {
	    PyErr_Format(PyExc_RuntimeError, "error accessing memory at %p", (void*)address);
	    return NULL;
    }

/*  if(address == 537851920) {
	    printf("bla: %i, type: %i\n", addr, type);
            unsigned long t = *(unsigned long *)addr;
	    printf("blu: %i\n", t);
    } */
    
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
	{"set_init_level4_pgt",     py_memory_set_init_level4_pgt,    METH_VARARGS, memory_set_init_level4_pgt__doc__},
	{"access",  py_memory_access, METH_VARARGS, memory_access__doc__},
	{"virt_to_phys", py_memory_virt_to_phys, METH_VARARGS, memory_virt_to_phys__doc__},
	{NULL, NULL}      /* sentinel */
};

PyMODINIT_FUNC
initmemory(void)
{
	Py_InitModule3("memory", memory_methods, memory__doc__);
}
