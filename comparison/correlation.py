import pandas
import seaborn
import matplotlib.pyplot as plt

import ccommon

def afrag_corr(afrag_file, pids, metrics=[i for i in range(len(ccommon._FUNC_NAMES))], method="kendall"):
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

