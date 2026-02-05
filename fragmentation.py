import lifetime_analysis
import MemoryModel
import common

import Sawicki_Arduino
import ebfm
import alternating_stream_entropy

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, ebfm.ebfm, Sawicki_Arduino.sawicki_arduino)

if __name__ == "__main__":
	common.arg_check()
	final_event = lifetime_analysis.parse_file()
	MemoryObjects = lifetime_analysis.objects
	memory_snapshot = MemoryModel.objects_to_snapshot(MemoryObjects)
	for f in _FRAG_FUNCTIONS:
		metric = f(memory_snapshot)
		print(f"{f.__name__}: {metric}")
