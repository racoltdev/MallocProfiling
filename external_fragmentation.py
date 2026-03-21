import common
import lifetime_analysis
import MemoryModel

def external_frag(snapshot):
	stream, _ = common.snapshot_to_free_block_stream(snapshot)
	# If nothing in stream, there is either no allocated mem, or no gaps in mem
	# It is safe to default to 0 fragmentation in these cases
	if len(stream) == 0:
		return 0
	else:
		free_size = sum(stream)
		free_max = max(stream)
		metric = 1 - (free_max / free_size)
		return metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = external_frag(memory_snapshot)
	print(f"external fragmentation: {frag_metric}")
