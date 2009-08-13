#/usr/bin/python

import os, re, string

# specify the defines which are to be extracted (as tuple of pairs)
# the filepath is relative to the kernel_base_path
defines = (('__PAGE_OFFSET', 'arch/x86/include/asm/page_64.h'),
	   ('__AC(X,Y)', 'include/linux/const.h'),)

# specify some helperdefines, which glue the extracted code together
helpers = (('_AC(X,Y)', '__AC(X,Y)'),)

incpipe = os.popen('echo -n /usr/src/linux-headers-`uname -r`')
kernel_base_path = incpipe.read()

# write output to this include file
incfile = open('kernel_defines.h', 'w')

print >>incfile, '#ifndef __KERNEL_INCLUDES_H'
print >>incfile, '#define __KERNEL_INCLUDES_H', '\n'

print >>incfile, '// define helper glue'

for l, r in helpers:
	print >>incfile, '#define ' + l + ' ' + r

print >>incfile, '\n'

endpat = re.compile("\\ ")

for name, path in defines:
	fullpath = kernel_base_path + "/" + path
	print 'extracting ' + name + ' from ' + fullpath
	fdesc = open(fullpath)
	namepat = re.compile('#define[ |\t]*' + name)
	inside = 0
	incomment = 0
	for line in fdesc:
		# linecomments
		kstart = string.find(line, '//')
		if kstart == 0:
			continue
		if kstart > 0:
			line = line[:kstart] + '\n'
		# multiline comments
		if incomment == 0:
			kstart = string.find(line, '/*')
			kend = string.find(line, '*/')
			if kstart > 0:
				incomment = 1
				if kend > kstart:
					incomment = 0
					b = line[:kstart]
					e = line[kend+2:]
					line = b + e
				else:
					line = line[:kstart] + '\n'
		else:
			kstart = string.find(line, '/*')
			kend = string.find(line, '*/')
			if kend > 0:
				incomment = 0
				if kstart > kend:
					incomment = 1
					line = line[kend+2:kstart] + '\n'
				else:
					line = line[kend+2:]
			else:
				continue
		# multiline defines with \ at the end of line
		if inside == 0:
			nret = namepat.search(line)
			if nret:
				ret = endpat.search(line)
				if ret:
					inside = 1
				print >>incfile, line,
		else:
			ret = endpat.search(line)
			if ret:
				inside = 1
			else:
				inside = 0
			print >>incfile, line,

print >>incfile, '#endif'

