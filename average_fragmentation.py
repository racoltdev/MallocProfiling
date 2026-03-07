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

def iter_avg(n, old_avg, new_val):
	avg = old_avg + (new_val - old_avg) / n
	return avg

# Collect average fragmentation rates of a multiprocess trace throughout it's entire lifetime
# Calculating fragmentation at every time stamp would be prohibitively expensive, so a snapshot
# is taken once every n timesteps and fragmentation is calculated at that timestep
# An average fragmentation rate for each metric is calculated between all timesteps and all processes
if __name__ == "__main__":
	trace_file = common.arg_check()
	metrics = {}
	lines = 0
	progress = 0

	with open(trace_file, 'r') as f:
		lines = sum(1 for line in f)

	print("Progress: 0%", end="")

	# This doesn't compute a true average since I'm not snapshotting at every event
	# Higher timestep means faster computation since fewer stream conversion have to be done
	# Lower timestep means higher accuracy and lower memory usage spikes
	for models, progress in mtrace_parser.parse(trace_file, 1000):
		for pid, model in models.items():
			if (model.alloc_blocks == {}):
				continue
			pid_avgs = metrics.get(pid, [0] * len(_FRAG_FUNCTIONS))
			# Why can't I just set the default with get 😭
			metrics[pid] = pid_avgs
			for i, func in enumerate(_FRAG_FUNCTIONS):
				func_avg = pid_avgs[i]
				print(metrics)
				print(pid_avgs)
				print(func_avg)
				metric = func(model)
				metrics[pid][i] = iter_avg(progress, func_avg, metric)
				# pid_metric_avgs[i].append(func(model))
				# metrics[pid] = pid_metric_avgs
		print("\rProgress: {:.3f} %".format(progress / lines * 100), end="")

	for pid in metrics.values():
		for i, method in enumerate(pid):
			pid[i] = float(numpy.average(method))
	print(f"pid, {[x.__name__ for x in _FRAG_FUNCTIONS]}")
	for k, v in metrics.items():
		print(f"{k}, {v}")

