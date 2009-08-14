all: memory.c bincmp.c
	python defineextractor.py
	python setup.py build
