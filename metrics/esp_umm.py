import lifetime_analysis
import MemoryModel
import common
import metrics.free_stream_cache as cache

import math

def ummfm(snapshot):
	if cache.stream is None:
		cache.stream, cache.length = common.snapshot_to_free_block_stream(snapshot)
	quality, free_size = 0, 0

	for f in cache.stream:
		quality += f**2
		free_size += f

	# If free_size == 0, then there is no used memory, or there are no gaps in memory
	# In this case, default to 0 fragmentation for this metric
	if free_size == 0:
		return 0
	else:
		quality_ratio = math.sqrt(quality) / free_size
		frag_metric = 1 - (quality_ratio**2)
		return frag_metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = esp_umm(memory_snapshot)
	print(f"esp_umm fragmentation: {frag_metric}")
