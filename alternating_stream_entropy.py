import lifetime_analysis
import MemoryModel
import common

def snapshot_to_alt_stream(memory_snapshot):
	alloc_blocks = memory_snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	alternating_stream = []
	sign = 1

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

def alt_stream_entropy(snapshot):
	stream = snapshot_to_alt_stream(snapshot)
	# encode n, rather than N. But should try with N
	# TODO replace n with N
	entropy_metric = common.entropy(stream)
	#print(f"metric: {entropy_metric / len(stream)}")
	return entropy_metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)#, event=1360)
	metric = alt_stream_entropy(memory_snapshot)
	print(f"alternating stream entropy metric: {metric}")
