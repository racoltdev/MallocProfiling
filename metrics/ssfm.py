import common
import lifetime_analysis
import MemoryModel
import metrics.free_stream_cache as cache

def ssfm(snapshot):
	if cache.stream is None:
		cache.stream, cache.length = common.snapshot_to_free_block_stream(snapshot)
	# Unlike external_fragmentation and esp_umm, this is well defined for all values
	# If nothing in stream, there is either no allocated mem, or no gaps in mem
	# It is safe to default to 0 fragmentation in these cases
	if len(cache.stream) == 0:
		return 0

	free_size = sum(cache.stream)
	free_max = max(cache.stream)
	corrected_external = free_max / (1 + free_size)
	partial_entropy = sum([f / cache.length for f in cache.stream])
	metric = (1 - corrected_external) * (1 - partial_entropy)
	return metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = ssfm(memory_snapshot)
	print(f"ssfm: {frag_metric}")
