#! /usr/bin/bash
# Run immediately after running { nohup bash -c "time LD_PRELOAD=/home/andy/Research/Kul/malloc/malloc/reduced_mtrace_malloc/libreduced_mtrace_malloc.so MALLOC_TRACE="/home/andy/Research/Kul/malloc/MallocProfiling/gcc/m.trace" make -j 8" ; } > ../results.out 2>&1 &
# RUN WITH NOHUP

kill_descendant_processes() {
    local pid="$1"
    local and_self="${2:-false}"
    if children="$(pgrep -P "$pid")"; then
        for child in $children; do
            kill_descendant_processes "$child" true
        done
    fi
    if [[ "$and_self" == true ]]; then
        kill -9 "$pid"
    fi
}

if [ $# -lt 1 ]; then
	echo "Missing required arguments"
	exit
fi
pid=$1
loops=0

while [ 1 ]; do
	size=$(ls -l /home/andy/Research/Kul/malloc/MallocProfiling/gcc/m.trace | awk '{print $5}');
	too_big=$((400 * 1024 * 1024 * 1024));
	if [ $((size)) -gt $too_big ]; then
		kill_descendant_processes $pid
		printf "\r%d: Killed process. Too many resources used\n" "$loops"
		exit;
	else
		loops=$((loops + 1))
		printf "\r%d: All good!" "$loops"
		sleep $((10));
	fi
done;
