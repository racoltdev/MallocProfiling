import sys
import os

import pickle

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import metrics.esp_umm as esp_umm
import metrics.ebfm as ebfm
import metrics.alternating_stream_entropy as alternating_stream_entropy
import metrics.external_fragmentation as external_fragmentation
import metrics.ssfm as ssfm
sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

_FUNC_NAMES = [x.__name__ for x in _FRAG_FUNCTIONS]

class AfragLine():
	def __init__(self, pid, metrics):
		self.pid = pid
		self.metrics = metrics

def read_line(pickle_file):
	with open(pickle_file, 'rb') as picklef:
		try:
			while True:
				yield pickle.load(picklef)
		except EOFError:
			pass

def parse_afrag_line(afrag_line):
	return AfragLine(afrag_line[0], afrag_line[1])
