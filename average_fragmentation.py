import common
import mptrace_parser
import printer
from cache import Cache, CacheItem
import sfrag

import metrics.esp_umm as esp_umm
import metrics.ebfm as ebfm
import metrics.alternating_stream_entropy as alternating_stream_entropy
import metrics.external_fragmentation as external_fragmentation
import metrics.ssfm as ssfm
import metrics.free_stream_cache as free_stream_cache

import os
import time
import pickle
import gzip

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

def weighted_moving_average(partial_avg, weight, new_val):
	partial_avg += (weight * new_val)
	return partial_avg

class PidCacheItem(CacheItem):
	def __init__(self, event_num, pid_avg):
		self.usage_hash = event_num
		self.pid_avg = pid_avg

	def pre_pickle(self):
		self.pid_avg = [x / self.usage_hash for x in self.pid_avg]

	def post_pickle(self):
		self.pid_avg = [x * self.usage_hash for x in self.pid_avg]

# Collect average fragmentation rates of a multiprocess trace throughout it's entire lifetime
# Calculating fragmentation at every time stamp would be prohibitively expensive, so a snapshot
# is taken once every n timesteps and fragmentation is calculated at that timestep
# An average fragmentation rate for each metric is calculated between all timesteps and all processes
if __name__ == "__main__":
	trace_file, output_file, verify = common.arg_check_io()
	sfrag_file = output_file + ".sfrag.gz"
	afrag_file = output_file + ".afrag.pickle"
	step_size = 10000

	sfragf = gzip.open(sfrag_file, "xb")
	pid_cache = Cache("pid_cache.pickle")
	file_size = os.path.getsize(trace_file)

	start_time = int(time.time())
	printer.progress(0, file_size, start_time)

	#sfragf.write(f"trace_line, {{pid: (pid_event_num, {[x.__name__ for x in _FRAG_FUNCTIONS]})}}\n")

	# This doesn't compute a true average since I'm not snapshotting at every event
	# Higher timestep means faster computation since fewer stream conversion have to be done
	# Lower timestep means higher accuracy and lower memory usage spikes
	for models, line_num, byte_pos in mptrace_parser.parse(trace_file, step_size, verify=verify):
		iter_metrics = {}
		for pid, model in models.items():
			# this never happens bc pids don't clean themselves up before exiting
			if (model.alloc_blocks == {}):
				continue

			n = model.events

			cached_item = pid_cache.get(pid, n)
			# pid not yet tracked in cache, initialize it
			if cached_item is None:
				cached_item = PidCacheItem(0, [0] * len(_FRAG_FUNCTIONS))
			# pid is stale, ignore it
			elif type(cached_item) is not PidCacheItem:
				continue

			old_n = cached_item.usage_hash

			iter_metrics[pid] = sfrag.PidMetrics(n, [0] * len(_FRAG_FUNCTIONS))

			for i, func in enumerate(_FRAG_FUNCTIONS):
				func_avg = cached_item.pid_avg[i]
				metric = func(model)

				iter_metrics[pid].func_metrics[i] = metric

				cached_item.pid_avg[i] = weighted_moving_average(func_avg, (n - old_n), metric)
			new_cache_item = PidCacheItem(n, cached_item.pid_avg)
			pid_cache.update(pid, new_cache_item)

			alternating_stream_entropy.reset_stream_cache()
			free_stream_cache.reset_stream_cache()

		pickle.dump((line_num, iter_metrics), sfragf)
		#sfragf.write(f"{line_num}, {iter_metrics}\n")
		printer.progress(byte_pos, file_size, start_time)

	sfragf.close()

	afragf = open(afrag_file, "xb")

	printer.printer(f"\n\nAverage fragmentation:\npid, {[x.__name__ for x in _FRAG_FUNCTIONS]}")
	#afragf.write(f"pid, {[x.__name__ for x in _FRAG_FUNCTIONS]}\n")

	for pid, cache_item in pid_cache.all():
		true_avg = [x / cache_item.usage_hash for x in cache_item.pid_avg]
		printer.printer(f"{pid}, {true_avg}")
		# afragf.write(f"{line}\n")
		pickle.dump((pid, true_avg), afragf)

	afragf.close()
	pid_cache.close_cache_file(destroy=True)
