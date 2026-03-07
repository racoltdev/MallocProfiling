#! /bin/bash
if [ $# -ne 2 ]; then
	echo "Error, expected 2 arguments:\n\ttracked PID\n\tfile to scan"
	exit
fi
PID=$1
f=$2
echo ; while $(ps -p $PID > /dev/null); do echo -en '\e[1A\e[K '; ls -lh $f ; sleep 1 ; done;
