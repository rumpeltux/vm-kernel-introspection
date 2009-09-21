
KERNEL_SOURCE = /usr/src/linux

all: memory.c bincmp.c kernel_defines.h
	python setup.py build

kernel_defines.h:
	python defineextractor.py --kernel $(KERNEL_SOURCE)

clean:
	python setup.py clean
	rm -rfv kernel_defines.h build/
