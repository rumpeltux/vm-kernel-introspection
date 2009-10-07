all:
	$(MAKE) -C /usr/src/linux-headers-`uname -r` M=$(PWD) \
                        $(filter-out all,$(MAKECMDGOALS))
	gcc -o giverewt giverewt.c

obj-m := taskigt.o

clean:
	rm *.o *.ko *.mod.c Module.markers Module.symvers modules.order
	rm giverewt

