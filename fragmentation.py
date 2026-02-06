import lifetime_analysis
import MemoryModel
import common

import esp_umm
import ebfm
import alternating_stream_entropy
import external_fragmentation
import ssfm

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	for f in _FRAG_FUNCTIONS:
		metric = f(memory_snapshot)
		print(f"{f.__name__}: {metric}")
