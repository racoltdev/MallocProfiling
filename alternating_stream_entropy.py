import math
import numpy

import lifetime_analysis
from MemoryModel import MemorySnapshot

# TODO fix class vs instance vars
class MemoryBlock:
	start_address = None
	end_address = None
	alloc = None
	free = None
	def __init__(self, start_address, end_address, alloc=True):
		self.start_address = start_address
		self.end_address = end_address
		self.free = not alloc
		self.alloc = alloc

def entropy(memory_stream):
	sum_entropy = 0
	for block in memory_stream:
		# encode n, rather than N. But should try with N
		frac = block / len(memory_stream)
		print(frac)
		sum_entropy += frac * (math.log(abs(frac)))
	return -sum_entropy

# Event is a single value representing one point in time - ie a snapshot
# lifetime_analysis generates range overlap data, a snapshot cannot do that
def construct_memory_snapshot(MemoryObjects, event=4):
	memory_snapshot = MemorySnapshot()
	sort_by_init = sorted(MemoryObjects.values(), key=lambda x: x.alloc_time)

	# TODO every allocated object should have size. Double check this

	for mem_object in sort_by_init:
		# Construct snapshot of memory at allocation event# "event"
		end_in_range = True if mem_object.dealloc_time is None else mem_object.dealloc_time > event

		if mem_object.alloc_time <= event and end_in_range:
			start_address = mem_object.address
			# Ignore any validation errors for now. Notifying in console is good enough
			memory_snapshot.malloc(start_address, mem_object.size)

	return memory_snapshot

def snapshot_to_alt_stream(memory_snapshot):
	# no more allocations will occur. allocation list can be sorted and the memory model can be discarded
	# sort by location in memory
	memory_snapshot.alloc_blocks = dict(sorted(memory_snapshot.alloc_blocks.items()))

	alloc_blocks = memory_snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	alternating_stream = []
	sign = 1

	#end = memory_snapshot.alloc_blocks.get(keys[-1]) + keys[-1]
	#print([numpy.binary_repr(x, width=64) for x in memory_snapshot.get_pages_in_range(keys[0], end)])

	# Assume memory begins at first allocation. This isn't realistic, but it balances out well enough
	# on large enough data. Can instead assume it lines up with nearest page of memory model.
	# mtrace doesn't give information about coallescing, so I'll just assume perfect coalescing for now.
	# Can modify this to assume worst case coalescing by creating individual free blocks for each item
	# deallocated prior to event.
	for i in range(len(keys) - 1):
		curr_block = (keys[i], alloc_blocks.get(keys[i]))
		next_block = (keys[i + 1], alloc_blocks.get(keys[i + 1]))

		alternating_stream.append(curr_block[1] * sign)

		# there is no free space between allocations
		if curr_block[0] + curr_block[1] == next_block[0]:
			sign *= -1
		else:
			alternating_stream.append((next_block[0] - (curr_block[0] + curr_block[1])) * sign)

	alternating_stream.append(alloc_blocks.get(keys[-1]))
	return alternating_stream

if __name__ == "__main__":
	lifetime_analysis.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = construct_memory_snapshot(MemoryObjects)#, event=1360)
	stream = snapshot_to_alt_stream(memory_snapshot)
	entropy_metric = entropy(stream)
	print(entropy_metric)
