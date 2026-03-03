import MemoryModel
import common
import mtrace_parser

import esp_ummm
import ebfm
import alternating_stream_entropy
import external_fragmentation
import ssfm

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

if __name__ == "__main__":
	trace_file = common.arg_check()
	metrics = {}
	metrics = [[] for x in _FRAG_FUNCTIONS]
	for models in mtrace_parser.parse(trace_file, 10000):
		for pid, model in models.items():
			for i, func in enumerate(_FRAG_FUNCTIONS):
				m_pid = metrics.get(pid, [[] for x in _FRAG_FUNCTIONS])
				m_pid[i].append(func(model))
				metrics[pid] = m_pid
