from distutils.core import setup, Extension
import os

incpipe = os.popen('echo -n /usr/src/linux-headers-`uname -r`/arch/x86/include')
kinc1 = incpipe.read()
incpipe = os.popen('echo -n /usr/src/linux-headers-`uname -r`/include')
kinc2 = incpipe.read()


setup(name="memory", version="0.1",
	ext_modules = [Extension("memory", 
				 include_dirs = [kinc1, kinc2],
				 sources = ["memory.c"])])

setup(name="bincmp", version="0.1",
	ext_modules = [Extension("bincmp", ["bincmp.c"])])
