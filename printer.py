last_progress_upd = None
last_msg_is_progress = False

def printer(msg, progress_msg=False):
	global last_msg_is_progress
	global last_progress_upd

	if last_msg_is_progress and progress_msg:
		last_progress_upd = msg
		print(f"\r{msg}", end='')

	elif last_msg_is_progress and not progress_msg:
		print(f"\r{msg}\n{last_progress_upd}", end='')

	elif not last_msg_is_progress and progress_msg:
		last_msg_is_progress = True
		last_progress_upd = msg
		print(msg, end='')

	elif not last_msg_is_progress and not progress_msg:
		print(msg)

