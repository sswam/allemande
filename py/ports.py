""" Allemande ports API, client library. """

import os
import time
from pathlib import Path
import itertools
import logging

import yaml
import inotify.adapters

logger = logging.getLogger(__name__)


def get_default_port(server):
	""" Get the default port for a server. """
	user_id = os.environ["USER"]
	default_ports_dir = Path(os.environ["ALLEMANDE_PORTS"])/server
	#default_port_id = f'{user_id}-{os.getpid()}'   # TODO?
	default_port_id = f'{user_id}'
	default_port = str(default_ports_dir/default_port_id)
	return default_port


# TODO use a client object

req_id = 0

def prepare_request(port, config=None):
	""" Make a request to the core server. """
	global req_id
	prep = port/"prep"
	req = prep/f"req-{req_id:06d}"
	req_id += 1

	# create the request directory, needs to be group writable
	umask = os.umask(0o007)
	try:
		req.mkdir(parents=True, exist_ok=True, mode=0o770)
	finally:
		os.umask(umask)

	if config:
		req_config = req/"config.yaml"
		req_config.write_text(yaml.dump(config))
	return req

def send_request(port, req):
	""" Send a request to the core server. """
	todo = port/"todo"
	req.rename(todo/req.name)

def wait_for_response(port, req):
	""" Wait for a response from the core server. """
	done = port/"done"
	error = port/"error"
	i = inotify.adapters.Inotify()

	# watch for the response dir in the done and error directories
	for path in [done, error]:
		i.add_watch(str(path), mask=inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_TO)

	resp = None

	# check if the response is already there
	for resp in itertools.chain(done.iterdir(), error.iterdir()):
		if resp.is_dir() and resp.name == req.name:
			status = resp.parent.name
			return resp, status

	# wait for the response
	for event in i.event_gen(yield_nones=False):
		(_, type_names, path, filename) = event
		logger.debug("PATH=[%r] FILENAME=[%r] EVENT_TYPES=%r", path, filename, type_names)
		path = Path(path)
		resp = path/filename
		if resp.is_dir() and filename == req.name:
			status = path.name
			return resp, status

	raise RuntimeError("no response")

def response_error(resp, raise_exception=True):
	""" Show the logs from a failed request. """
	log = resp/"log.txt"
	if log.exists():
		log_text = log.read_text()
		logger.error("request failed: %s", log_text)
		raise RuntimeError(f"request failed: {log_text}")

def remove_response(port, resp):
	""" Move a response to the history directory. """
	history = port/"history"
	while True:
		history_name = f"{time.time():.2f}-{resp.name}"
		try:
			resp.rename(history/history_name)
			break
		except FileExistsError:
			pass
