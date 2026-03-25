import math
import sys

def snapshot_to_free_block_stream(memory_snapshot):
	alloc_blocks = memory_snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	stream = []

	length = (keys[-1] + alloc_blocks.get(keys[-1])) - keys[0]

	for i in range(len(keys) - 1):
		curr_block = (keys[i], alloc_blocks.get(keys[i]))
		next_block = (keys[i + 1], alloc_blocks.get(keys[i + 1]))

		curr_end = curr_block[0] + curr_block[1]
		if curr_end != next_block[0]:
			stream.append(next_block[0] - curr_end)

	return stream, length

def entropy(stream, length=None):
	length = length if length else len(stream)
	sum_entropy = 0
	for block in stream:
		frac = block / length
		sum_entropy += frac * math.log(abs(frac))
	return -sum_entropy

def arg_check():
	if len(sys.argv) != 2:
		print("Error: Incorrect number of arguments. Please pass the path to a trace file")
		exit()
	return sys.argv[1]

# TODO use argparse for input handling
def arg_check_io():
	args = len(sys.argv)
	if args == 3:
		return *sys.argv[1:], True
	elif args == 4:
		verify = sys.argv[-1].lower()
		if verify == "true":
			return *sys.argv[1:-1], True
		elif verify == "false":
			return *sys.argv[1:-1], False
		else:
			print("Error: Invalid argument. Optional third argument 'verify' must be either True or False")
			exit()
	else:
		print("Error: Incorrect number of arguments. Expected 2.\n\tInput mptrace file\n\tOutput file\n\tOptional: Perform verification bool. Defaults to True.")
		exit()
