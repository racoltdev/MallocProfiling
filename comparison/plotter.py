import math
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
	#type_names = ["tracked_value", "low", "high"]
	#metric_names = func_names + "mem_size"

	col_names = ["time", "type", "metric name", "metric"]

	dfs = {i : pandas.DataFrame(columns=col_names) for i in metrics}
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
			dfs[i].loc[len(dfs[i])] = new_row
			#print(new_row)

	def normalize(dfs):
		pass

	events = 0
	for pid in pids:
		for line in ccommon.read_line(sfrag_file, gz=True):
			if pid in line.segment_metrics.keys():
				pid_metrics = line.segment_metrics.get(pid)
				#print(line.event_num)
				#print(pid_metrics.func_metrics)

				func_metrics = [metric for i, metric in enumerate(pid_metrics.func_metrics) if i in metrics]
				make_rows(dfs, func_metrics, line.event_num, "tracked value")
				new_row = [line.event_num, "tracked value", "mem size", pid_metrics.mem_bounds]
				dfs["mem_size"].loc[len(dfs["mem_size"])] = new_row
				#print(new_row)
				#input()

				if bounded:
					low, high = get_metric_bounds(line)

					make_rows(dfs, low, line.event_num, "low")
					make_rows(dfs, high, line.event_num, "high")

				events += 1
				if event_limit is not None and events > event_limit:
					break

	for key, df in dfs.items():
		#print(df.to_string())
		#dfs[key]["metric"] = (df["metric"]-df["metric"].mean())/df["metric"].std()
		df["metric"] = (df["metric"] - df["metric"].min()) / (df["metric"].max() - df["metric"].min())
		#dfs[key]["metric"] = df["metric"].map(lambda x: math.log(x + 0.001))
		dfs[key]["metric"] = df["metric"]
		#print(dfs[key].to_string())
	df = pandas.concat(dfs.values(), ignore_index=True)

	ccommon.vprint(df)
	seaborn.lineplot(data=df, x="time", y="metric", style="type", hue="metric name")
	plt.show()

