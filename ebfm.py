import entropy_base
import lifetime_analysis
import MemoryModel

def snapshot_to_ebfm_stream(memory_snapshot):
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

def ebfm(MemoryObjects):
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	stream, length = snapshot_to_ebfm_stream(memory_snapshot)
	entropy_metric = entropy_base.entropy(stream, length)
	print(f"EBFM: {entropy_metric}")

if __name__ == "__main__":
	lifetime_analysis.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	ebfm(MemoryObjects)
