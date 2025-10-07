import matplotlib.pyplot as plt
import sys
import random

# Reference glibc-2.42/malloc/mtrace-impl.c
# This parses mtrace log files to track object alloc and free events
# The source for mtrace is the only reference I could find on these log files
# See `man mtrace 1` for a tool to parse mtrace log files and find all memory leaks

objects = {}
valid_ops = ['-', '+', '!', '>', '<']

class MemObject:
	dealloc_time = None
	def __init__(self, address, size, alloc_time):
		self.address = address
		self.size = size
		self.alloc_time = alloc_time


def parse_log_line(line, num):
	line = line.split()
	op = line[2]
	if len(op) != 1 or op not in valid_ops:
		print(f"Warning! Could not parse line {num}:")
		print(f"\t{line}")
	try:
		address = int(line[3], 16)
		size = None
		if len(line) == 5:
			size = int(line[4], 16)
	except:
		# Sometimes you'll see a line like
		# `@ ./raColTest:[0xecac] - + 0x5591547cd7f0 0x55`
		# The first sign seems to be an offset direction marker. Hard to tell. I think only the second one is useful to me
		op = line[3]
		address = int(line[4], 16)
		size = None
		if len(line) == 5:
			size = int(line[5], 16)
	return address, op, size


def remap_obj(address, size, num):
	new_hash = random.random()
	while objects.get(new_hash) is not None:
		new_hash = random.random()
	objects[new_hash] = objects[address]
	objects[address] = MemObject(address, size, num)


def track_obj(address, op, size, num):
	tracked_obj = objects.get(address)
	if tracked_obj is None:
		if op == "<":
			# pointer realloc'd before being assigned. ignore this
			print("warn: pointer realloc'd before being assigned @ {hex(address)}, :{num}")
			pass
		else:
			objects[address] = MemObject(address, size, num)
			if op == '-' or op == "!":
				objects[address].dealloc_time = num
	else:
		# Free or null ptr assignment
		if op == "-":
			# reusing already freed memory
			if tracked_obj.dealloc_time:
				remap_obj(address, size, num)
			else:
				tracked_obj.dealloc_time = num
		# Alloc
		elif op == "+":
			if tracked_obj.dealloc_time:
				# reusing already freed memory
				remap_obj(address, size, num)
			else:
				# error: double assigning memory. do not track this
				print(f"Warn: double assigning memory @ {hex(address)}, :{num}")
				pass
		# Alloc fail
		elif op == "!":
			# realloc failed. ignore
			print("realloc failed")
			pass
		# ptr realloc'd
		elif op == "<":
			if tracked_obj.dealloc_time:
				# double freeing. ignore
				print("Warn:double freeing @ {hex(address)}, :{num}")
				pass
			else:
				tracked_obj.dealloc_time = num
		# new address from realloc
		elif op == ">":
			if tracked_obj.dealloc_time:
				# reusing already freed memory
				remap_obj(address, size, num)
			else:
				# error: double assigning memory. do not track this
				print("Warn: double assigning memory @ {hex(address)}, :{num}")
				pass


def plot_obj(obj, y, axis):
	if (obj.dealloc_time - obj.alloc_time) < 1:
		axis.plot(obj.alloc_time, y, 'bo')
		print(f"Temp object @ {hex(obj.address)}, :{obj.alloc_time}")
	else:
		axis.plot([obj.alloc_time, obj.dealloc_time], [y, y])

def main():
	if len(sys.argv) != 2:
		print("Incorrect number of arguments. Please pass the path to a trace file")
		exit()

	final_event = 0
	with open(sys.argv[1], 'r') as log_file:
		random.seed()
		header = log_file.readline()
		if header != "= Start\n":
			print("Argument error! Supplied file is not an mtrace logfile")
			exit()

		for num, line in enumerate(log_file, 1):
			address, op, size = parse_log_line(line, num)
			track_obj(address, op, size, num)
			final_event = num

	fig, ax = plt.subplots()
	# TODO sort objects first to make graph easier to read
	for num, obj in enumerate(objects.values()):
		if obj.dealloc_time is None:
			print(f"Object @ {hex(obj.address)} was never freed!")
			final_event += 1
			obj.dealloc_time = final_event
		plot_obj(obj, num, ax)
	ax.set(xlabel="Allocation event number", ylabel="Tracked object ID", title=f"Object lifetimes of {sys.argv[1]}")
	plt.show()

if __name__ == "__main__":
	main()
