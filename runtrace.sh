#! /usr/bin/bash

LD_PRELOAD=/lib/$(gcc -print-multiarch)/libc_malloc_debug.so.0 MALLOC_TRACE="./m.trace" ./mtrace_launcher $@
