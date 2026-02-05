import lifetime_analysis
import MemoryModel
import entropy_base

import math

def snapshot_to_free_block_stream(memory_snapshot):
	alloc_blocks = memory_snapshot.alloc_blocks
	keys = list(alloc_blocks.keys())
	stream = []

	for i in range(len(keys) - 1):
		curr_block = (keys[i], alloc_blocks.get(keys[i]))
		next_block = (keys[i + 1], alloc_blocks.get(keys[i + 1]))

		curr_end = curr_block[0] + curr_block[1]
		if curr_end != next_block[0]:
			stream.append(next_block[0] - curr_end)

	return stream

def sawicki_arduino(snapshot):
	stream = snapshot_to_free_block_stream(snapshot)
	quality, free_size = 0, 0

	for f in stream:
		quality += f**2
		free_size += f
	quality_ratio = math.sqrt(quality) / free_size
	frag_metric = 1 - (quality_ratio**2)
	return frag_metric

if __name__ == "__main__":
	lifetime_analysis.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = sawicki_arduino(memory_snapshot)
	print(f"Sawicki-Arduino fragmentation: {frag_metric}")
