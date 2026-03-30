import pandas
import seaborn
import matplotlib.pyplot as plt

import ccommon

def afrag_spearman_corr(afrag_file, pids, metrics=[i for i in range(len(ccommon._FUNC_NAMES))]):
	all_pids = True if pids == [] else False

	col_names = [metric for i, metric in enumerate(ccommon._FUNC_NAMES) if i in metrics]
	df = pandas.DataFrame(columns=col_names)

	for line in ccommon.read_line(afrag_file):
		if all_pids or line.pid in pids:
			new_row = [metric for i, metric in enumerate(line.metrics) if i in metrics]
			df.loc[len(df)] = new_row

	corr = df.corr(method="kendall")

	seaborn.heatmap(corr, cmap="flare", annot=True)

	plt.title(afrag_file)
	plt.show()

