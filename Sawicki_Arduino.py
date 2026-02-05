import lifetime_analysis
import MemoryModel
import common

import math

def sawicki_arduino(snapshot):
	stream, _ = common.snapshot_to_free_block_stream(snapshot)
	quality, free_size = 0, 0

	for f in stream:
		quality += f**2
		free_size += f
	quality_ratio = math.sqrt(quality) / free_size
	frag_metric = 1 - (quality_ratio**2)
	return frag_metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = sawicki_arduino(memory_snapshot)
	print(f"Sawicki-Arduino fragmentation: {frag_metric}")
