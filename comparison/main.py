import argparse
import sys
import os
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import metrics.esp_umm as esp_umm
import metrics.ebfm as ebfm
import metrics.alternating_stream_entropy as alternating_stream_entropy
import metrics.external_fragmentation as external_fragmentation
import metrics.ssfm as ssfm
sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import correlation

_FRAG_FUNCTIONS = (alternating_stream_entropy.alt_stream_entropy, alternating_stream_entropy.norm_alt_entropy, ebfm.ebfm, esp_umm.esp_umm, external_fragmentation.external_frag, ssfm.ssfm)

_FUNC_NAMES = [x.__name__ for x in _FRAG_FUNCTIONS]

def create_parser():
	ap = argparse.ArgumentParser(add_help=True)

	source_select = ap.add_mutually_exclusive_group(required=True)
	source_select.add_argument("--avg", action="store_true", help="If selected, use an afrag file as input")
	source_select.add_argument("--segment", action="store_true", help="If selected, use an sfrag file as input")

	ap.add_argument("--afrag", type=str, help="Path to an afrag.pickle file")
	ap.add_argument("--sfrag", type=str, help="Path to an sfrag.pickle.gzip file")

	pid_select = ap.add_mutually_exclusive_group(required=True)
	pid_select.add_argument("-p", "--pid", action="extend", nargs="+", type=int, \
			help="A list of PIDs to compare")
	pid_select.add_argument("--pr", "--random-pid-count", type=int, help="The number of PIDs to randomly sample \
			from the given afrag file")
	pid_select.add_argument("--pc", "--first-n-pids", type=int, help="Sample the first n PIDs from the given \
			given afrag file")

	ap.add_argument("--spearman", action="store_true", help="If selected, perform spearman rank correlation")

	ap.add_argument("--metrics", dest="metrics", action="extend", nargs="+", \
			default=_FUNC_NAMES, choices=_FUNC_NAMES, type=str)

	ap.add_argument("--seed", help="A seed to use for all random numbers. Defaults to current system time")


def err_check(args):
	if args.pid is None and args.afrag == None: ap.error("Automatic sampling of pids requires passing an afrag file with the --afrag argument")

	if args.avg and args.afrag is None:
		ap.error("If avg option is used, an input file must be passed with --afrag")
	elif args.segment and args.sfrag is None:
		ap.error("If segment option is used, an input file must be passed with --sfrag")


def pid_init(args):
	def read_line(afrag):
		with open(afrag, 'rb') as afragf:
	        try:
	            while True:
	                yield pickle.load(afragf)[0]
	        except EOFError:
	            yield None

	if args.pid is not None:
		pass

	elif args.pc is not None:
		for i in range(args.pc):
			pid = read_line(args.afrag)
			if pid is None:
				break
			args.pid.append(pid)

	elif args.pr is not None:
		all_pid = []
		for pid in read_line(args.afrag):
			all_pid.append(pid)
		args.pid = random.sample(all_pid, args.pr)


def args():
	ap = create_parser()
	args = ap.parse_args()
	err_check(args)

	# Extra initializations
	random.seed(args.seed)



if __name__ == "__main__":
	args = args()
	if args.avg and args.spearman:
		correlation.afrag_spearman_corr(args.afrag, args.pid
