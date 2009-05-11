from distutils.core import setup, Extension

setup(name="memory", version="0.1",
	ext_modules = [Extension("memory", ["memory.c"])])

