import lifetime_analysis
import MemoryModel
import common

stream = None

# This and snapshot_to_free_stream are the biggest bottlenecks of the whole program.
# If it continues to be a problem, c or inline assembly will be needed.
# I can't make python do this any faster.
# Could replace stream generation every loop with stream updating every loop. This
# would need a complex caching system and reworking my whole stack. Absolute last
# resort option.
def snapshot_to_alt_stream(memory_snapshot):
	alloc_blocks = memory_snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	alternating_stream = []
	sign = 1

	last_bound = None
	# Assume memory begins at first allocation. This isn't realistic, but it balances out well enough
	# on large enough data. Can instead assume it lines up with nearest page of memory model.
	# mtrace doesn't give information about coallescing, so I'll just assume perfect coalescing for now.
	# Can modify this to assume worst case coalescing by creating individual free blocks for each item
	# deallocated prior to event.
	for i in range(len(keys)):
		start = keys[i]
		length = alloc_blocks.get(keys[i])

		alternating_stream.append(length * sign)

		if last_bound is not None:
			touching = last_bound == start
			if touching:
				sign *= -1

		last_bound = start + length
	return alternating_stream

def aefm(snapshot):
	global stream
	if stream is None:
		stream = snapshot_to_alt_stream(snapshot)
	# encode n, rather than N. But should try with N
	# TODO replace n with N
	entropy_metric = common.entropy(stream)
	#print(f"metric: {entropy_metric / len(stream)}")
	return entropy_metric

def naefm(snapshot):
	global stream
	if stream is None:
		stream = snapshot_to_alt_stream(snapshot)

	alloc_blocks = snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	length = (keys[-1] + alloc_blocks.get(keys[-1])) - keys[0]

	entropy_metric = common.entropy(stream, length)
	return entropy_metric

def reset_stream_cache():
	global stream
	stream = None

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)#, event=1360)
	memory_snapshot.alloc_blocks = dict(sorted(memory_snapshot.alloc_blocks.items()))
	metric = alt_entropy(memory_snapshot)
	print(f"alternating entropy metric: {metric}")
	norm_metric = norm_alt_entropy(memory_snapshot)
	print(f"normalized alternating entropy metric: {norm_metric}")
