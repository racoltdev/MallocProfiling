import MemoryModel
import common
import mptrace_parser
from printer import printer

import metrics.esp_umm as esp_umm
import metrics.ebfm as ebfm
import metrics.alternating_stream_entropy as alternating_stream_entropy
import metrics.external_fragmentation as external_fragmentation
import metrics.ssfm as ssfm

import os
import time
import pickle

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

def weighted_moving_average(partial_avg, weight, new_val):
	partial_avg += (weight * new_val)
	return partial_avg

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

class PidPickle:
	def __init__(self, pid_avg, model):
		self.pid_avg = pid_avg
		self.model = model

# Collect average fragmentation rates of a multiprocess trace throughout it's entire lifetime
# Calculating fragmentation at every time stamp would be prohibitively expensive, so a snapshot
# is taken once every n timesteps and fragmentation is calculated at that timestep
# An average fragmentation rate for each metric is calculated between all timesteps and all processes
if __name__ == "__main__":
	trace_file, output_file = common.arg_check_io()
	sfrag_file = output_file + ".sfrag"
	afrag_file = output_file + ".afrag"
	avg_metrics = {}
	iter_metrics = {}
	stale_pids = {}
	cached_pids = {}
	step_size = 10000
	# staled, unstaled, pickled, unpickled = 0, 0, 0, 0

	sfragf = open(sfrag_file, "x")
	stalef = open("stale_pids.pickle", "w+b")
	file_size = os.path.getsize(trace_file)

	start_time = int(time.time())
	progress_bar(0, file_size, start_time)

	sfragf.write(f"trace_line, {{pid: (pid_event_num, {[x.__name__ for x in _FRAG_FUNCTIONS]})}}\n")

	# This doesn't compute a true average since I'm not snapshotting at every event
	# Higher timestep means faster computation since fewer stream conversion have to be done
	# Lower timestep means higher accuracy and lower memory usage spikes
	for models, line_num, byte_pos in mptrace_parser.parse(trace_file, step_size):
		for pid, model in models.items():
			n = model.events

			# this never happens bc pids don't clean themselves up before exiting
			if (model.alloc_blocks == {}):
				continue

			# This extra staging uses a lot more branching and moving
			# but turns out much more efficient since most pids are very short lived
			# Removing them from memory lets this work on large datasets
			elif pid in stale_pids:
				if n == stale_pids.get(pid)[0]:
					# pid is super stale, save state to json in case it needs to be revived
					# can never assume pid is dead, so these all may become active again
					pid_avg = [x / stale_pids[pid][0] for x in avg_metrics[pid]]
					pid_pickle = PidPickle(pid_avg, model)
					cached_pids[pid] = (stalef.tell(), n)
					pickle.dump(pid_pickle, stalef)
					del stale_pids[pid]
					del avg_metrics[pid]
					# pickled += 1
					continue
				else:
					# pid is no longer stale, unstage it
					iter_metrics[pid] = stale_pids[pid]
					del stale_pids[pid]
					# unstaled += 1

			old_n = 0

			# if pid is stale, stage it for removal
			if pid in iter_metrics:
				old_n = iter_metrics.get(pid)[0]
				if n == old_n:
					stale_pids[pid] = iter_metrics.get(pid)
					del iter_metrics[pid]
					# staled += 1
					continue

			# recover cached pids from pickle file
			elif pid in cached_pids and n > cached_pids[pid][1]:
				stalef.seek(cached_pids[pid][0])

				pid_pickle = pickle.load(stalef)
				avg_metrics[pid] = pid_pickle.pid_avg
				cached_model = pid_pickle.model
				# merge dicts together, with latter dicts overwriting previous keys if overlap
				# hopefully by restoring blocks and pages, this shouldn't damage state
				model.alloc_blocks = {**cached_model.alloc_blocks, **model.alloc_blocks}
				model.pages = {**cached_model.pages, **model.pages}
				old_n = cached_pids[pid][1]

				del cached_pids[pid]
				# seek to end of file
				stalef.seek(0, 2)
				# unpickled += 1

			pid_avgs = avg_metrics.get(pid, [0] * len(_FRAG_FUNCTIONS))
			# Why can't I just set the default with get 😭
			avg_metrics[pid] = pid_avgs

			iter_metrics[pid] = (n, [0] * len(_FRAG_FUNCTIONS))

			for i, func in enumerate(_FRAG_FUNCTIONS):
				func_avg = pid_avgs[i]
				metric = func(model)

				iter_metrics[pid][1][i] = metric
				avg_metrics[pid][i] = weighted_moving_average(func_avg, (n - old_n), metric)

		sfragf.write(f"{line_num}, {iter_metrics}\n")
		progress_bar(byte_pos, file_size, start_time)

	sfragf.close()
	stalef.close()
	os.remove("stale_pids.pickle")

	for pid, val in stale_pids.items():
		iter_metrics[pid] = val

	del stale_pids

	afragf = open(afrag_file, "x")

	printer(f"\n\nAverage fragmentation:\npid, {[x.__name__ for x in _FRAG_FUNCTIONS]}")
	afragf.write(f"pid, {[x.__name__ for x in _FRAG_FUNCTIONS]}\n")
	for pid, avg_frag in avg_metrics.items():
		line = f"{pid}, {[x / iter_metrics[pid][0] for x in avg_frag]}"
		printer(line)
		afragf.write(f"{line}\n")

	afragf.close()
	print()
	# print(f"Staled {staled} pids")
	# print(f"Unstaled {unstaled} pids")
	# print(f"Pickled {pickled} pids")
	# print(f"Unpickled {unpickled} pids")
