import time

last_progress_upd = None
last_msg_is_progress = False

# This makes sure progress updates are always at the bottom of screen
# and don't interfere with other log messages
def printer(msg, progress_msg=False):
	global last_msg_is_progress
	global last_progress_upd

	if last_msg_is_progress and progress_msg:
		last_progress_upd = msg
		print(f"\r{msg}", end='')

	elif last_msg_is_progress and not progress_msg:
		# \033[K completely clears the current line
		print(f"\r\033[K{msg}\n{last_progress_upd}", end='')

	elif not last_msg_is_progress and progress_msg:
		last_msg_is_progress = True
		last_progress_upd = msg
		print(msg, end='')

	elif not last_msg_is_progress and not progress_msg:
		print(msg)

def progress(completed, total, start_time, bar_length=40):
	progress = int((completed / total) * bar_length)
	done = "█" * progress
	not_done = "-" * (bar_length - progress)
	bar = done + not_done

	percent = f"{((completed / total) * 100):.2f}%"

	current_time = int(time.time())
	elapsed_time = current_time - start_time
	elapsed_day = elapsed_time / (60 * 60 * 24)
	format_elapsed = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

	estimated_end_time = 0;
	# Catch divide by zero errors
	if (completed != 0):
		estimated_end_time = int(elapsed_time * (total / completed))
	estimated_end_day = estimated_end_time / (60 * 60 * 24)
	estimated_end_format =  time.strftime("%H:%M:%S", time.gmtime(estimated_end_time))

	printer(f"{percent} [{bar}] | {elapsed_day}D+{format_elapsed}<{estimated_end_day}D+{estimated_end_format}", True)
