import common
import lifetime_analysis
import MemoryModel

def ebfm(snapshot):
	stream, length = common.snapshot_to_free_block_stream(snapshot)
	entropy_metric = common.entropy(stream, length)
	return entropy_metric

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	metric = ebfm(memory_snapshot)
	print(f"EBFM: {metric}")
