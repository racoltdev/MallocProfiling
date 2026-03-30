from typing import Dict

class PidMetrics:
	def __init__(self, event_num : int, func_metrics : list):
		self.event_num = event_num
		self.func_metrics = func_metrics

class SfragLine:
	def __init__(self, event_num : int, segment_metrics : Dict[str, PidMetrics]):
		self.event_num = event_num
		self.segment_metrics = segment_metrics

class AfragLine:
	def __init__(self, pid, metrics : list):
		self.pid = pid
		self.metrics = metrics
