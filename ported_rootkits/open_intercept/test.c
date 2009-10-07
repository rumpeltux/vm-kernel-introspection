#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init_task.h>
#include <linux/unistd.h>
#include <linux/syscalls.h>
#include <linux/file.h>
#include <linux/fs.h>
#include <asm/unistd.h>
#include <asm/cacheflush.h>

// from system.map
/* ffffffff802e1fc0 sys_open
   ffffffff802e1d40 sys_close
   ffffffff802e49a0 sys_read */

#define SYS_OPEN_ADDR 0xffffffff802e1fc0
#define SYS_CLOSE_ADDR 0xffffffff802e1d40
#define SYS_READ_ADDR 0xffffffff802e49a0

void** sys_call_table = NULL;

/* asmlinkage long sys_close(unsigned int fd);
asmlinkage ssize_t sys_read(unsigned int fd, char __user *buf, size_t count);
asmlinkage long sys_open(const char __user *filename, int flags, int mode); */

long (*orig_sys_open)(const char __user *filename, int flags, int mode);

asmlinkage long my_sys_open(const char __user *filename, int flags, int mode) {
	printk(KERN_INFO"hook called\n");
	return orig_sys_open(filename, flags, mode);
}

#define PAGE_BOUNDARY_ADDR(x) (__pa((x)) >> PAGE_SHIFT)

int set_page_rw(void* addr) {
	return set_memory_rw(PAGE_BOUNDARY_ADDR(addr), 1);	
}

int init_module(void)
{
/*	unsigned long *ptr;
	// ptr=(unsigned long *)((init_mm.end_code + 8) & 0xfffffffc);
	ptr=(unsigned long *)((init_mm.end_code + 4) & 0xfffffffffffffffc);
	printk(KERN_INFO"startsearch: %p\n", ptr);
	while((unsigned long )ptr < (unsigned long)init_mm.end_data) {
		if ((unsigned long *)*ptr == (unsigned long *)SYS_OPEN_ADDR) {
			printk(KERN_INFO" -> matching detected at %p\n", ptr);
			if ( (unsigned long *)*((ptr-__NR_open)+__NR_read) == (unsigned long *)SYS_READ_ADDR && 
				(unsigned long*)*((ptr-__NR_open)+__NR_open) == (unsigned long*)SYS_OPEN_ADDR)
			{
				sys_call_table = ((unsigned long *)(ptr-__NR_close));
				break;
			}
		}
		ptr++;
	}

	printk(KERN_INFO"sys_call_table base found at: %p\n", sys_call_table);
	
	if (sys_call_table == NULL) {
		printk(KERN_INFO "sys_call_table == NULL\n");
	} */

	// we do no calculation we just take the value from System.map
//	sys_call_table = (void**)0xffffffff806a18e0;
	sys_call_table = (void**)0xffffffff806aa7f0;

	printk(KERN_INFO"sys_call_table[0] = %p\n", sys_call_table[0]);
	printk(KERN_INFO"__NR_open: %i\n", __NR_open);
	printk(KERN_INFO"sys_call_table[__NR_open] = %p\n", sys_call_table[__NR_open]);
	printk(KERN_INFO"&sys_call_table[__NR_open]: %p\n", &sys_call_table[__NR_open]);
	
	printk(KERN_INFO"backup\n");
	orig_sys_open = sys_call_table[__NR_open];
	printk(KERN_INFO"orig_sys_open: %p\n", orig_sys_open);

//	printk(KERN_INFO"set_memory_rw\n");
//	set_page_rw(&sys_call_table[__NR_open]);
	printk(KERN_INFO"replace\n");
	sys_call_table[__NR_open] = my_sys_open; 

	return 0;
}


void cleanup_module(void)
{
	sys_call_table[__NR_open] = orig_sys_open;
}

MODULE_LICENSE("GPL");
