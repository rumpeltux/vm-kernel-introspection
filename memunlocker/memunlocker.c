/*
 * This Module uses kretprobes to circumvent the restriction of access to /dev/mem
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/limits.h>

MODULE_PARM_DESC(func, "Module to unlock the /dev/mem device for unrestricted access");

/* Here we use the entry_hanlder to timestamp function entry */
static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	if (!current->mm)
		return 1;	/* Skip kernel threads */

	return 0;
}

static int ret_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	regs->ax = 1;
	return 0;
}

static struct kretprobe my_kretprobe = {
	.handler		= ret_handler,
	.entry_handler		= entry_handler,
	.data_size		= 0,
	.maxactive		= 20,
};

static int __init kretprobe_init(void)
{
	int ret;

	my_kretprobe.kp.symbol_name = "devmem_is_allowed";
	ret = register_kretprobe(&my_kretprobe);
	if (ret < 0) {
		printk(KERN_INFO "register_kretprobe failed, returned %d\n",
				ret);
		return -1;
	}
	printk(KERN_INFO "Planted return probe at %s: %p\n",
			my_kretprobe.kp.symbol_name, my_kretprobe.kp.addr);
	return 0;
}

static void __exit kretprobe_exit(void)
{
	unregister_kretprobe(&my_kretprobe);
	printk(KERN_INFO "kretprobe at %p unregistered\n",
			my_kretprobe.kp.addr);

	/* nmissed > 0 suggests that maxactive was set too low. */
	printk(KERN_INFO "Missed probing %d instances of %s\n",
		my_kretprobe.nmissed, my_kretprobe.kp.symbol_name);
}

module_init(kretprobe_init)
module_exit(kretprobe_exit)
MODULE_LICENSE("GPL");
