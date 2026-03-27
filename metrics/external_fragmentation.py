import common
import lifetime_analysis
import MemoryModel
import metrics.free_stream_cache as cache

def external_frag(snapshot):
	if cache.stream is None:
		cache.stream, cache.length = common.snapshot_to_free_block_stream(snapshot)
	# If nothing in stream, there is either no allocated mem, or no gaps in mem
	# It is safe to default to 0 fragmentation in these cases
	free_size = sum(cache.stream)
	if free_size == 0:
		return 0
	else:
		free_max = max(cache.stream)
		metric = 1 - (free_max / free_size)
		return metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = external_frag(memory_snapshot)
	print(f"external fragmentation: {frag_metric}")
