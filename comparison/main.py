print("Importing libraries...")
import argparse
import sys
import os
import random

import plotter
import ccommon

def create_parser():
	def get_file_contents(fname):
		with open(fname, 'r') as f:
			return f.read()

	ap = argparse.ArgumentParser(add_help=True, \
			description="""This is a complex interface for generating visualization from sfrag and afrag files. \
Read the argument descriptions carefully and see the examples section to see how this is used in practice""", \
			epilog=get_file_contents("usage.txt"), \
			formatter_class=argparse.RawDescriptionHelpFormatter, \
	)

	source_select = ap.add_mutually_exclusive_group(required=True)
	source_select.add_argument("--avg", action="store_true", help="If selected, use an afrag file as input")
	source_select.add_argument("--segment", action="store_true", help="If selected, use an sfrag file as input")

	ap.add_argument("--afrag", type=str, help="Path to an afrag.pickle file")
	ap.add_argument("--sfrag", type=str, help="Path to an sfrag.pickle.gzip file")

	pid_select = ap.add_mutually_exclusive_group(required=True)
	pid_select.add_argument("-p", "--pid", action="extend", nargs="+", \
			help="A list of PIDs to compare. Each PID must be an integer-like string.", default=[])
	pid_select.add_argument("--pr", "--random-pid-count", type=int, help="The number of PIDs to randomly sample \
			from the given afrag file")
	pid_select.add_argument("--pc", "--first-n-pids", type=int, help="Sample the first n PIDs from the given \
			afrag file")
	pid_select.add_argument("--pa", "--all-pids", action="store_true", help="Do not perform pid sampling. Use \
			all	pids in the given afrag file")
	pid_select.add_argument("--pm", "--most-used-pid", action="store_true", help="Only track the pid with the most \
			allocation events")

	ap.add_argument("--correlation", choices=["pearson", "spearman", "kendall"], help="If selected perform \
			the listed type of correlation")
	ap.add_argument("--lifetime", nargs="?", default=None, const="unbounded", choices=["bounded", "unbounded"], \
			help="If selected, plot a line chart of the selected metrics and pids throughout their lifetime. If \
			an additional \"bounded\" argument is given, also plot the highest and lowest scoring pids for each \
			metric at each timestep.")

	ap.add_argument("--metrics", nargs="+", \
			default=ccommon._FUNC_NAMES, choices=ccommon._FUNC_NAMES, type=str)

	ap.add_argument("--seed", help="A seed to use for all random numbers. Defaults to current system time")
	ap.add_argument("-e", "--event_limit", type=int, help="If supplied, only process {x} number of allocation events \
			and then exit. This is useful when plotting from a very large sfrag file")
	ap.add_argument("--verbose", action="store_true")

	return ap


def err_check(args, ap):
	if args.pid is None and not args.pa and args.afrag == None:
		ap.error("Automatic sampling of pids requires passing an afrag file with the --afrag argument")

	if args.avg and args.afrag is None:
		ap.error("If avg option is used, an input file must be passed with --afrag")
	elif args.segment and args.sfrag is None:
		ap.error("If segment option is used, an input file must be passed with --sfrag")

	if not args.segment and args.lifetime:
		ap.error("Lifetime plotting requires an sfrag file and selecting --segment")


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

	elif args.pm:
		pids = {}
		for line in ccommon.read_line(args.afrag):
			pids[line.pid] = line.event_count
		args.pid = [sorted(pids, key=pids.get)[-1]]


def metrics_init(args):
	indexed_metrics = []
	for metric in args.metrics:
		indexed_metrics.append(ccommon._FUNC_NAMES.index(metric))

	args.metrics = sorted(indexed_metrics)


def get_args():
	ap = create_parser()
	args = ap.parse_args()
	err_check(args, ap)

	# Extra initializations
	random.seed(args.seed)
	pid_init(args)
	metrics_init(args)

	return args

if __name__ == "__main__":
	print("Continuing\n")
	args = get_args()
	ccommon.vprint(args, verbose=args.verbose)

	if args.avg and args.correlation:
		plotter.afrag_corr(args.afrag, args.pid, args.metrics, args.correlation)
	elif args.segment and args.correlation:
		raise NotImplementedError("Correlation across an sfrag file is not implemented")

	if args.segment and args.lifetime:
		bounded = True if args.lifetime == "bounded" else False
		plotter.sfrag_lifetime(args.sfrag, args.pid, args.metrics, args.event_limit, bounded)

	plot = args.correlation or args.lifetime
	if not plot:
		ccommon.vprint("No action selected")

	ccommon.vprint("Done!")
