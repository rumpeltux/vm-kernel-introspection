#!/bin/bash
#

if [ $# -le 0 ] ; then
	echo "usage: $0 <output_filename_text>"
	exit 1
fi

cat "$1" | grep differing: | awk '// {print $2}' | awk -F '.' '// {print $1}' | sort | uniq | grep -v '^$'
