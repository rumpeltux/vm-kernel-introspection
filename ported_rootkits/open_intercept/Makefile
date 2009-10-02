all:
	$(MAKE) -C /usr/src/linux-headers-`uname -r` M=$(PWD) \
                        $(filter-out all,$(MAKECMDGOALS))

obj-m := test.o

clean:
	rm *.o *.ko *.mod.c Module.markers Module.symvers modules.order

