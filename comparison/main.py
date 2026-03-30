print("Importing libraries...")
import argparse
import sys
import os
import random

import correlation
import ccommon

def create_parser():
	ap = argparse.ArgumentParser(add_help=True)

	source_select = ap.add_mutually_exclusive_group(required=True)
	source_select.add_argument("--avg", action="store_true", help="If selected, use an afrag file as input")
	source_select.add_argument("--segment", action="store_true", help="If selected, use an sfrag file as input")

	ap.add_argument("--afrag", type=str, help="Path to an afrag.pickle file")
	ap.add_argument("--sfrag", type=str, help="Path to an sfrag.pickle.gzip file")

	pid_select = ap.add_mutually_exclusive_group(required=True)
	pid_select.add_argument("-p", "--pid", action="extend", nargs="+", type=int, \
			help="A list of PIDs to compare", default=[])
	pid_select.add_argument("--pr", "--random-pid-count", type=int, help="The number of PIDs to randomly sample \
			from the given afrag file")
	pid_select.add_argument("--pc", "--first-n-pids", type=int, help="Sample the first n PIDs from the given \
			afrag file")
	pid_select.add_argument("--pa", "--all-pids", action="store_true", help="Do not perform pid sampling. Use all \
			pids in the given afrag file")

	ap.add_argument("--spearman", action="store_true", help="If selected, perform spearman rank correlation")

	ap.add_argument("--metrics", dest="metrics", action="extend", nargs="+", \
			default=ccommon._FUNC_NAMES, choices=ccommon._FUNC_NAMES, type=str)

	ap.add_argument("--seed", help="A seed to use for all random numbers. Defaults to current system time")

	return ap


def err_check(args):
	if args.pid is None and not args.pa and args.afrag == None:
		args.error("Automatic sampling of pids requires passing an afrag file with the --afrag argument")

	if args.avg and args.afrag is None:
		args.error("If avg option is used, an input file must be passed with --afrag")
	elif args.segment and args.sfrag is None:
		args.error("If segment option is used, an input file must be passed with --sfrag")


def pid_init(args):
	if args.pid != [] or args.pa:
		pass

	elif args.pc is not None:
		for i, line in enumerate(ccommon.read_line(args.afrag)):
			if i >= args.pc:
				break
			args.pid.append(line.pid)
		if args.pc >= len(args.pid):
			print(f"[ArgParser] Warn: Requested {args.pc} samples, but only {len(args.pid)} samples exist in provided file")

	elif args.pr is not None:
		all_pid = []
		for line in ccommon.read_line(args.afrag):
			all_pid.append(line.pid)

		if args.pr >= len(all_pid):
			print(f"[ArgParser] Warn: Requested {args.pr} samples, but only {len(all_pid)} samples exist in provided file")
			args.pr = len(all_pid) - 1
		args.pid = random.sample(all_pid, args.pr)


def metrics_init(args):
	indexed_metrics = []
	for metric in args.metrics:
		if metric in ccommon._FUNC_NAMES:
			indexed_metrics.append(ccommon._FUNC_NAMES.index(metric))

	args.metrics = sorted(indexed_metrics)


def get_args():
	ap = create_parser()
	args = ap.parse_args()
	err_check(args)

	# Extra initializations
	random.seed(args.seed)
	pid_init(args)
	metrics_init(args)

	return args

if __name__ == "__main__":
	print("Continuing\n")
	args = get_args()
	if args.avg and args.spearman:
		correlation.afrag_spearman_corr(args.afrag, args.pid, args.metrics)
