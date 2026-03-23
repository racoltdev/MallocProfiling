import MemoryModel
from printer import printer

def parse_line(line, num):
	valid_ops = ['-', '+', '!', '>', '<']

	line = line.split()
	pid = line[0]
	op = line[2]
	if len(op) != 1 or op not in valid_ops:
		printer(f"Error: Could not parse line {num}:")
		printer(f"\t{line}")

	address = int(line[3], 16)
	size = None
	if len(line) == 5:
		size = int(line[4], 16)
		# On some systems, malloc(0) returns a pointer instead of null. This obviously takes allocation
		# space and must be accounted for. See `man malloc`
		if size == 0:
			size = 1

	return pid, address, op, size


def track_obj(pid, address, op, size, num, models, verify):
	pid_mem = models.get(pid, MemoryModel.MemorySnapshot(max_depth=2, verify=verify))
	#print(pid_mem.alloc_blocks)

	obj = pid_mem.alloc_blocks.get(address)
	if obj is None:
		if op == "<":
			# realloc((void*)null, (int)x) isn't an error, but mtrace should not write "<" in this case. "+" is preferable.
			printer(f"""[Parser] Error: pointer realloc'd before being assigned @ {hex(address)}, :{num}\n
\tThere is an error in your log file, tracer, or allocator!""")
		elif op == '-':
			printer(f"[Parser] Warn: object free'd before being assigned @ {hex(address)}, :{num}")
		elif op == "!":
			printer(f"[Parser] Info: realloc failed on null pointer, :{num}")
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
			printer(f"[Parser] Warn: double assigning memory @ {hex(address)}, :{num}")
		# Alloc fail
		elif op == "!":
			# realloc failed. Don't track
			printer(f"[Parser] Info: realloc failed @ {hex(address)} to size {hex(size)}, :{num}")
		# ptr realloc'd
		elif op == "<":
			pid_mem.free(address)
		# new address from realloc
		elif op == ">":
			# double assigning memory. do not track this
			printer("[Parser] Warn: double assigning memory @ {hex(address)}, :{num}")
	models[pid] = pid_mem
	#print("\n\n")


def parse(trace_file, limit, verify=True):
	models = {}
	num = 0
	last_pos = 0

	# f.tell() may be inaccurate if not using binary mode depending on non-ascii chars and os
	# with open is much faster than f = open()
	with open(trace_file, 'rb') as f:
		# Ignore existance of Start line if its there
		start = f.tell()

		# [2: to remove "b'"
		# [:-3] to remove "\\n"
		header = str(f.readline())[2:-3]
		if header != "= Start":
			f.seek(start)

		for num, line in enumerate(f, 1):
			obj = parse_line(str(line)[2:-3], num)
			track_obj(*obj, num, models, verify)
			if num % limit == 0:
				# Will return models even if no events occured to that pid this timestep
				# This is innefficient but doesn't harm anything
				yield (models, num, f.tell())

		last_pos = f.tell()

	yield (models, num, last_pos)
