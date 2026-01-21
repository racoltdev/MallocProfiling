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

def construct_memory(MemoryObjects, event):
	memory_snapshot = MemorySnapshot()
	sort_by_init = sorted(MemoryObjects.values(), key=lambda x: x.alloc_time)
	lowest_address = -1
	highest_address = -1
	for mem_object in sort_by_init:
		if lowest_address == -1 or mem_object.address < lowest_address:
			lowest_address = mem_object.address
		# TODO every allocated object should have size. Double check this
		if mem_object.size and (highest_address == -1 or (mem_object.address + mem_object.size - 1) > highest_address):
			highest_address = mem_object.address + mem_object.size - 1
	print(hex(lowest_address), hex(highest_address))
	print(hex(highest_address - lowest_address))

	for mem_object in sort_by_init:
		# Construct snapshot of memory at allocation event# "event"
		end_in_range = True if mem_object.dealloc_time is None else mem_object.dealloc_time > event
		if mem_object.alloc_time <= event and end_in_range:
			start_address = mem_object.address
			end_address = start_address + mem_object.size - 1
			print("{0:#016x}, {1:#016x}".format(start_address, end_address))
			# Ignore any validation errors for now. Notifying in console is good enough
			memory_snapshot.malloc(start_address, end_address)

	# no more allocations will occur. allocation list can be sorted and the memory model can be discarded
	memory_snapshot.alloc_blocks = dict(sorted(memory_snapshot.alloc_blocks.items()))

	print(memory_snapshot.alloc_blocks)
	print(memory_snapshot.pages)
	keys = list(memory_snapshot.alloc_blocks.keys())
	end = memory_snapshot.alloc_blocks.get(keys[-1])
	print([numpy.binary_repr(x, width=64) for x in memory_snapshot.get_pages_in_range(keys[0], end)])
	exit()
	# mtrace doesn't give information about coallescing, so I'll just assume perfect coalescing for now.
	# Can modify this to assume worst case coalescing by creating individual free blocks for each item
	# deallocated prior to event.
	for i in range(len(memory_snapshot)):
		i_word = memory_snapshot[i]
		if not i_word:
			span = 1
			for j in range(i + 1, len(memory_snapshot)):
				j_word = memory_snapshot[j]
				if not j:
					span += 1
				else:
					break
			block = MemoryBlock(i, span + i, alloc=False)
			for j in range(i, span + i):
				memory_snapshot[j] = block
			i += span - 1

	return memory_snapshot

if __name__ == "__main__":
	lifetime_analysis.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = construct_memory(MemoryObjects, event=4)
