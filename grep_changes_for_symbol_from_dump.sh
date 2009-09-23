#!/bin/bash
#

if [ $# -le 1 ] ; then
	echo "usage: $0 <output text dump filename> <symbol name"
	exit 1
fi

cat "$1" | grep "differing: *$2\." | awk '// {print $2}'
