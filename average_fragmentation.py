import MemoryModel
import common
import mptrace_parser
from printer import printer

import esp_umm
import ebfm
import alternating_stream_entropy
import external_fragmentation
import ssfm

import os
import time
import sys

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

def iter_avg(n, old_avg, new_val, weight=1.0):
	avg = old_avg + (((new_val - old_avg) * weight) / n)
	return avg

def progress_bar(completed, total, start_time, bar_length=40):
	progress = int((completed / total) * bar_length)
	done = "█" * progress
	not_done = "-" * (bar_length - progress)
	bar = done + not_done

	percent = f"{((completed / total) * 100):.2f}%"

	current_time = int(time.time())
	elapsed_time = current_time - start_time
	format_elapsed = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

	estimated_end_time = 0;
	# Catch divide by zero errors
	if (completed != 0):
		estimated_end_time = int(elapsed_time * (total / completed))
	estimated_end_format =  time.strftime("%H:%M:%S", time.gmtime(estimated_end_time))

	printer(f"{percent} [{bar}] | {format_elapsed}<{estimated_end_format}", True)

# Collect average fragmentation rates of a multiprocess trace throughout it's entire lifetime
# Calculating fragmentation at every time stamp would be prohibitively expensive, so a snapshot
# is taken once every n timesteps and fragmentation is calculated at that timestep
# An average fragmentation rate for each metric is calculated between all timesteps and all processes
if __name__ == "__main__":
	trace_file, output_file = common.arg_check_io()
	avg_metrics = {}
	step_size = 10000

	outf = open(output_file, "x")
	file_size = os.path.getsize(trace_file)

	start_time = int(time.time())
	progress_bar(0, file_size, start_time)

	outf.write(f"trace_line, {{pid, pid_event_num {[x.__name__ for x in _FRAG_FUNCTIONS]}}}\n")

	# This doesn't compute a true average since I'm not snapshotting at every event
	# Higher timestep means faster computation since fewer stream conversion have to be done
	# Lower timestep means higher accuracy and lower memory usage spikes
	for models, line_num, byte_pos in mptrace_parser.parse(trace_file, step_size):
		iter_metrics = {}
		for pid, model in models.items():
			if (model.alloc_blocks == {}):
				continue

			pid_avgs = avg_metrics.get(pid, [0] * len(_FRAG_FUNCTIONS))
			# Why can't I just set the default with get 😭
			avg_metrics[pid] = pid_avgs

			n = model.events
			# n really isn't needed in the key, but it makes printing n easier
			key = f"{pid}, {n}"
			iter_metrics[key] = iter_metrics.get(pid, [0] * len(_FRAG_FUNCTIONS))

			for i, func in enumerate(_FRAG_FUNCTIONS):
				func_avg = pid_avgs[i]
				metric = func(model)

				iter_metrics[key][i] = metric
				avg_metrics[pid][i] = iter_avg(n, func_avg, metric)

		outf.write(f"{line_num}, {iter_metrics}\n")
		progress_bar(byte_pos, file_size, start_time)

	printer(f"\n\nAverage fragmentation:\npid, {[x.__name__ for x in _FRAG_FUNCTIONS]}")
	outf.write(f"\n\nAverage fragmentation:\npid, {[x.__name__ for x in _FRAG_FUNCTIONS]}\n")
	for pid, avg_frag in avg_metrics.items():
		line = f"{pid}, {avg_frag}"
		printer(line)
		outf.write(f"{line}\n")

	outf.close()
	print()
