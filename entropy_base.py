import math

def entropy(stream, length=None):
	length = length if length else len(stream)
	sum_entropy = 0
	for block in stream:
		frac = block / length
		sum_entropy += frac * math.log(abs(frac))
	return -sum_entropy
