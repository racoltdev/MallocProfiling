import pandas
import seaborn
import matplotlib.pyplot as plt

import ccommon

def _get_col_names(metrics):
	col_names = [metric for i, metric in enumerate(ccommon._FUNC_NAMES) if i in metrics]

def afrag_corr(afrag_file, pids, metrics, method="kendall"):
	all_pids = True if pids == [] else False

	col_names = [metric for i, metric in enumerate(ccommon._FUNC_NAMES) if i in metrics]
	df = pandas.DataFrame(columns=col_names)

	for line in ccommon.read_line(afrag_file):
		if all_pids or line.pid in pids:
			new_row = [metric for i, metric in enumerate(line.metrics) if i in metrics]
			df.loc[len(df)] = new_row

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
	col_names = ["time", "type", "metric name", "metric"]
	df = pandas.DataFrame(columns=col_names)

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

	def make_rows(df, func_metrics, event_num, type_name):
		for metric, name in zip(func_metrics, func_names):
			new_row = [event_num, type_name, name, metric]
			df.loc[len(df)] = new_row

	events = 0
	for pid in pids:
		for line in ccommon.read_line(sfrag_file, gz=True):
			if pid in line.segment_metrics.keys():
				pid_metrics = line.segment_metrics.get(pid)

				func_metrics = [metric for i, metric in enumerate(pid_metrics.func_metrics) if i in metrics]
				make_rows(df, func_metrics, line.event_num, "tracked value")
				new_row = [line.event_num, "tracked value", "mem size", pid_metrics.mem_bounds]
				df.loc[len(df)] = new_row

				low, high = get_metric_bounds(line)

				make_rows(df, low, line.event_num, "low")
				make_rows(df, high, line.event_num, "high")
				events += 1

				ccommon.vprint(df)

				if event_limit is not None and events > event_limit:
					break

	print()
	print(df)
	seaborn.lineplot(data=df, x="time", y="metric", style="type", hue="metric name")
	plt.show()

