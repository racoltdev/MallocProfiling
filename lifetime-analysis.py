import matplotlib.pyplot as plt
import sys
import random

objects = {}
valid_ops = ['-', '+', '!', '>', '<']

class MemObject:
	dealloc_time = None
	def __init__(self, address, op, size, alloc_time):
		self.address = address
		self.op = op
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
		# The second sign seems to be an offset direction marker. Hard to tell. I think only the first one is useful to me
		address = int(line[4], 16)
		size = None
		if len(line) == 5:
			size = int(line[5], 16)
	return address, op, size


def remap_obj(address, op, size, num):
	objects[random.random] = objects[address]
	objects[address] = MemObject(address, op, size, num)
	objects[address].dealloc_time = num

def main():
	if len(sys.argv) != 2:
		print("Incorrect number of arguments. Please pass the path to a trace file")
		exit()

	with open(sys.argv[1], 'r') as log_file:
		random.seed()
		header = log_file.readline()
		if header != "= Start\n":
			print("Argument error! Supplied file is not an mtrace logfile")
			exit()

		for num, line in enumerate(log_file, 1):
			address, op, size = parse_log_line(line, num)
			tracked_obj = objects.get(address)
			if tracked_obj is None:
				if op == "<":
					# pointer realloc'd before being assigned. ignore this
					pass
				else:
					objects[address] = MemObject(address, op, size, num)
					if op == '-' or op == "!":
						objects[address].dealloc_time = num
			else:
				# Free or null ptr assignment
				if op == "-":
					# reusing already freed memory
					if tracked_obj.dealloc_time:
						remap_obj(address, op, size, num)
					else:
						tracked_obj.dealloc_time = num
				# Alloc
				elif op == "+":
					if tracked_obj.dealloc_time:
						# reusing already freed memory
						remap_obj(address, op, size, num)
					else:
						# error: double assigning memory. do not track this
						pass
				# Alloc fail
				elif op == "!":
					# realloc failed. ignore
					pass
				# ptr realloc'd
				elif op == "<":
					if tracked_obj.dealloc_time:
						# double freeing. ignore
						pass
					else:
						tracked_obj.dealloc_time = num
				# new address from realloc
				elif op == ">":
					if tracked_obj.dealloc_time:
						# reusing already freed memory
						remap_obj(address, op, size, num)
					else:
						# error: double assigning memory. do not track this
						pass



if __name__ == "__main__":
	main()
