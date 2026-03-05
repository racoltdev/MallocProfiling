import common
import lifetime_analysis
import MemoryModel

def ssfm(snapshot):
	stream, length = common.snapshot_to_free_block_stream(snapshot)
	# TODO check if 0 is right for this case
	if len(stream) == 0:
		return 0

	free_size = sum(stream)
	free_max = max(stream)
	corrected_external = free_max / (1 + free_size)
	partial_entropy = sum([f / length for f in stream])
	metric = (1 - corrected_external) * (1 - partial_entropy)
	return metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	frag_metric = ssfm(memory_snapshot)
	print(f"ssfm: {frag_metric}")
