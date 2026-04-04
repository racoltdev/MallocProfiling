import math
import pandas
import seaborn
import matplotlib.pyplot as plt
import numpy

import ccommon

def afrag_corr(afrag_file, pids, metrics, method="kendall"):
	all_pids = True if pids == [] else False

	col_names = [metric for i, metric in enumerate(ccommon._FUNC_NAMES) if i in metrics]
	df = pandas.DataFrame(columns=col_names)

	#df["metric"] = (df["metric"] - df["metric"].min()) / (df["metric"].max() - df["metric"].min())
	for line in ccommon.read_line(afrag_file):
		if all_pids or line.pid in pids:
			new_row = [metric for i, metric in enumerate(line.metrics) if i in metrics]
			df.loc[len(df)] = new_row

	# normalize each metric. For spearman and kednall this really should matter but¯\(ツ)/¯
	df=(df-df.min())/(df.max()-df.min())

	corr = df.corr(method=method)
	# Sort cols and rows by sum of correlations
	corr = corr[sorted(corr.columns, key=lambda col: corr[col].sum())]
	corr = corr.reindex(list(corr.columns))

	seaborn.heatmap(corr, cmap="flare", annot=True)

	file_name = afrag_file.split("/")[-1]
	plt.title(f"{file_name} {method} correlation")
	plt.show()


def sfrag_lifetime(sfrag_file, pids, metrics, event_limit, bounded):
	# for now, assume a single pid. Can add support for multi axis later
	if len(pids) != 1:
		raise NotImplementedError("Lifetime can only be plotted for one pid at a time, currently")

	func_names = [metric for i, metric in enumerate(ccommon._FUNC_NAMES) if i in metrics]
	#type_names = ["tracked_value", "low", "high"]
	#metric_names = func_names + "mem_size"

	col_names = ["time", "type", "metric name", "metric"]

	dfs = {i : pandas.DataFrame(columns=col_names) for i in func_names}
	dfs = dict(sorted(dfs.items()))
	dfs["mem_size"] = pandas.DataFrame(columns=col_names)

	def get_metric_bounds(line):
		low, high = {}, {}
		# get min and max values for each metric at this time stamp
		for pid, pid_metrics in line.segment_metrics.items():
			for metric in metrics:
				func_metric = pid_metrics.func_metrics
				if low.get(metric) is None or low.get(metric) > func_metric[metric]:
					low[metric] = func_metric[metric]
				if high.get(metric) is None or high.get(metric) < func_metric[metric]:
					high[metric] = func_metric[metric]

		return low, high

	def make_rows(dfs, func_metrics, event_num, type_name):
		for i, (metric, name) in enumerate(zip(func_metrics, func_names)):
			new_row = [event_num, type_name, name, metric]
			dfs[name].loc[len(dfs[name])] = new_row

	events = 0
	for pid in pids:
		for line in ccommon.read_line(sfrag_file, gz=True):
			if pid in line.segment_metrics.keys():
				pid_metrics = line.segment_metrics.get(pid)

				func_metrics = [metric for i, metric in enumerate(pid_metrics.func_metrics) if i in metrics]
				#print(func_metrics)
				make_rows(dfs, func_metrics, line.event_num, "tracked value")
				new_row = [line.event_num, "tracked value", "mem size", pid_metrics.mem_bounds]
				dfs["mem_size"].loc[len(dfs["mem_size"])] = new_row

				if bounded:
					low, high = get_metric_bounds(line)
					make_rows(dfs, low.values(), line.event_num, "low")
					make_rows(dfs, high.values(), line.event_num, "high")

				events += 1
				if event_limit is not None and events > event_limit:
					break

	for key, df in dfs.items():
		# both of these outlier methods don't work all that well
		#df["metric"] = df["metric"].map(lambda x: numpy.sqrt(x))
		#winsorize(df["metric"], limits=[0.1, 0.25])

		# TODO normalization doesn't work with bounded plotting
		tracked = df[df["type"] == "tracked value"]
		tracked = tracked["metric"]
		df["metric"] = (df["metric"] - tracked.min()) / (tracked.max() - tracked.min())
		#df["metric"] = df["metric"].map(lambda x: numpy.sqrt(x))
		dfs[key]["metric"] = df["metric"]
	df = pandas.concat(dfs.values(), ignore_index=True)

	ccommon.vprint(df)
	seaborn.lineplot(data=df, x="time", y="metric", style="type", hue="metric name")
	plt.title(f"{sfrag_file} lifetime")
	plt.show()

