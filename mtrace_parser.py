import MemoryModel

def parse_line(line, num):
	valid_ops = ['-', '+', '!', '>', '<']

	line = line.split()
	pid = line[0]
	op = line[2]
	if len(op) != 1 or op not in valid_ops:
		print(f"Error: Could not parse line {num}:")
		print(f"\t{line}")

	address = int(line[3], 16)
	size = None
	if len(line) == 5:
		size = int(line[4], 16)

	return pid, address, op, size


def track_obj(pid, address, op, size, num, models):
	pid_mem = models.get(pid, MemoryModel.MemorySnapshot(max_depth=2))
	#print(pid_mem.alloc_blocks)

	obj = pid_mem.alloc_blocks.get(address)
	if obj is None:
		if op == "<":
			# realloc((void*)null, (int)x) isn't an error, but mtrace should not write "<" in this case. "+" is preferable.
			print(f"""[Parser] Error: pointer realloc'd before being assigned @ {hex(address)}, :{num}\n
\tThere is an error in your log file, tracer, or allocator!""")
		elif op == '-':
			print(f"[Parser] Warn: object free'd before being assigned @ {hex(address)}, :{num}")
		elif op == "!":
			print(f"[Parser] Info: realloc failed on null pointer, :{num}")
		else:
			pid_mem.malloc(address, size)
			#print(pid_mem)
	else:
		# Free or null ptr assignment
		if op == "-":
			pid_mem.free(address)
		# Alloc
		elif op == "+":
			# error: double assigning memory. Do not track this
			print(f"[Parser] Warn: double assigning memory @ {hex(address)}, :{num}")
		# Alloc fail
		elif op == "!":
			# realloc failed. Don't track
			print(f"[Parser] Info: realloc failed @ {hex(address)} to size {hex(size)}, :{num}")
		# ptr realloc'd
		elif op == "<":
			pid_mem.free(address)
		# new address from realloc
		elif op == ">":
			# double assigning memory. do not track this
			print("[Parser] Warn: double assigning memory @ {hex(address)}, :{num}")
	models[pid] = pid_mem
	#print("\n\n")


def parse(trace_file, limit):
	models = {}
	num = 0

	# f.tell() may be inaccurate if not using binary mode depending on non-ascii chars and os
	with open(trace_file, 'rb') as f:
		# Ignore existance of Start line if its there
		start = f.tell()
		header = str(f.readline())
		if header != "= Start\n":
			f.seek(start)

		for num, line in enumerate(f, 1):
			obj = parse_line(str(line)[1:-3], num)
			track_obj(*obj, num, models)
			if num % limit == 0:
				yield (models, num, f.tell())

	yield (models, num, f.tell())
