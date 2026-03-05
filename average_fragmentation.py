import MemoryModel
import common
import mtrace_parser

import esp_umm
import ebfm
import alternating_stream_entropy
import external_fragmentation
import ssfm

import numpy

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

if __name__ == "__main__":
	trace_file = common.arg_check()
	metrics = {}
	lines = 0
	progress = 0

	with open(trace_file, 'r') as f:
		lines = sum(1 for line in f)

	print("Progress: 0%", end="")

	# This doesn't compute a true average since som PIDs don't exist for a full timestep
	# Higher timestep means faster computation since fewer stream conversion have to be done
	# Lower timestep means higher accuracy and lower memory usage spikes
	for models, progress in mtrace_parser.parse(trace_file, 1000):
		for pid, model in models.items():
			if (model.alloc_blocks == {}):
				continue
			for i, func in enumerate(_FRAG_FUNCTIONS):
				m_pid = metrics.get(pid, [[] for x in _FRAG_FUNCTIONS])
				m_pid[i].append(func(model))
				metrics[pid] = m_pid
		print("\rProgress: {:.3f} %".format(progress / lines * 100), end="")

	for pid in metrics.values():
		for i, method in enumerate(pid):
			pid[i] = float(numpy.average(method))
	print(f"pid, {[x.__name__ for x in _FRAG_FUNCTIONS]}")
	for k, v in metrics.items():
		print(f"{k}, {v}")

