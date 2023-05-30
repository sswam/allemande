# this l library is in the public domain
# Sam Watkins, 2012

import sys
from os import path, makedirs, rename, remove
import datetime
from time import time, sleep
import subprocess
import re
import json
from decimal import *

prog_path = None
prog_dir = None
prog = None
debug_on = [False]

a_day = datetime.timedelta(1)

raise_exception = {}

def set_debug(on):
	debug_on[0] = on

def init(prog_file):
	global prog, prog_path, prog_dir
	prog_path = prog_file
	prog_dir = path.dirname(prog_file)
	prog = path.basename(prog_file)

def make_list(x):
	if x.__class__ != list:
		x = [x]
	return x

def warn(s):
	sys.stderr.write("WARN: "+s+"\n")

def debug(s):
	if debug_on[0]:
		sys.stderr.write("DEBUG: "+s+"\n")

def debug_timestamp(s):
	debug(timestamp()+": "+s)

def error(s):
	sys.stderr.write("ERROR: "+s+"\n")
	exit(1)

def usage(s):
	sys.stderr.write("usage: %s %s\n" % (prog, s))
	exit(2)

def resource(file):
	return path.relpath(file, prog_dir)

def warn_exception():
	warn("exception: " + repr(sys.exc_info()))

def debug_exception():
	debug("exception: " + repr(sys.exc_info()))

def ymd(date):  # datetime.date
	return date.strftime("%Y%m%d")

def repr_list_float(list, decimals, none='None'):
	fmt = "%%.%df" % decimals
	s = "["+", ".join([none if f is None else fmt % f for f in list])+"]"
	return s

def split_list(s, delim=','):
	return [i for i in s.split(delim) if i != '']

def join_list(l, delim=','):
	return delim.join([str(x) for x in l])

# thanks to http://www.peterbe.com/plog/uniqifiers-benchmark
def uniq(seq, idfun=None):
	if idfun is None:
		idfun = lambda x: x
	seen = {}
	result = []
	for item in seq:
		marker = idfun(item)
		if marker in seen: continue
		seen[marker] = 1
		result.append(item)
	return result

def mkdirs(dir):
	try:
		makedirs(dir)
	except:
		pass

def mkparents(filename):
	mkdirs(path.dirname(filename))


def file_put(filename, content, atomic=False):
	mkparents(filename)
	if atomic:
		dir, base = path.split(filename)
		newfile = path.join(dir, "."+base+".new")  # not unique
		file_put(newfile, content)
		rename(newfile, filename)
	else:
		with open(filename, "w") as out:
			out.write(content)

def file_get(filename, default=raise_exception):
	if default != raise_exception:
		try:
			x = file_get(filename, default=raise_exception)
			return x
		except:
			return default
	with open(filename, "r") as inp:
		return "".join(inp.readlines())

def timestamp(secs=None, fmt="%Y-%m-%d %H:%M:%S"):
	if secs is None:
		dt = datetime.datetime.now()
	else:
		dt = datetime.datetime.fromtimestamp(secs)
	return dt.strftime(fmt)

def file_cache(dict, path, mode):
	if dict.has_key(path):
		return dict[path]
	fh = dict[path] = open(path, mode)
	return fh

# TODO pairwise is just zip now in Python 3?
def pairwise(t):
	it = iter(t)
	return zip(it,it)  # was itertools.izip

web_timeout = 15
web_retries = 3

def web_config(timeout, retries):
	web_timeout = timeout
	web_retries = retries

def web_get_1(url):
	proc = subprocess.Popen(["curl", "-f", "--max-time", str(int(web_timeout)), "--compressed", "--", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(out, err) = proc.communicate()
	retcode = proc.poll()
	if retcode:
		raise Exception("failed: web_get: "+str(err))
#	if out is None or out == '':
#		raise Exception("failed: web_get")
	return out

def web_get(url):
	return retry(fn=lambda: web_get_1(url))

def hms(secs):
	return timestamp(secs, fmt="%H:%M:%S")

def sleep_to(wake_time):
	delay = wake_time - time()
	if delay > 0:
		if delay > 2:
			debug("sleeping for %.0fs to %s" % (delay, hms(wake_time)))
		sleep(delay)

def future(delay):
	return time() + delay

def retry(times=web_retries, fn=None):
	if not fn:
		raise Exception("retry: must provide fn argument")
	for i in range(0, times):
		try:
			return fn()
		except:
			warn("retry: operation failed %d/%d" % (i+1, times))
			debug_exception()
			if i == times - 1:
				raise

def int_or_zero(s, not_int=0):
	if (re.match(r'-?\d+$', s)):
		return int(s)
	return not_int

def app(l, item):
	l = l.append(item)
	return l

def put(d, k, v):
	d[k] = v
	return d

# TODO Warn of weird values
def float_or_none(s):
	try:
		return float(s)
	except:
		return None

# TODO Warn of weird values
def int_or_none(s):
	try:
		return int(s)
	except:
		return None

def json_q(s):
	if s is None:
		return 'null'
	s = s.replace('\\', '\\\\')
	s = s.replace('\'', '\\\'')
	s = s.replace('\n', '\\n')
	return "'%s'" % s

def fix_floats(json, decimals=6, quote='"'):
	pattern = r'^((?:(?:"(?:\\.|[^\\"])*?")|[^"])*?)(-?\d+\.\d{'+str(decimals)+'}\d+)'
	pattern = re.sub('"', quote, pattern)
	fmt = "%%.%df" % decimals
	n = 1
	while n:
		json, n = re.subn(pattern, lambda m: m.group(1)+(fmt % float(m.group(2))).rstrip('0'), json)
	return json

def json_dump(data, decimals=2):
	s = json.dumps(data, separators=(',',':'), sort_keys=True)
	s = fix_floats(s, decimals=decimals)
	return s

def try_remove(file):
	try:
		remove(file)
		return True
	except:
		return False

def dict_vals(d, list_of_keys):
	return [d[k] for k in list_of_keys]

def dict_decimal_to_float(a_dict):
	for k in a_dict:
		if type(a_dict[k]) == Decimal:
			a_dict[k] = float(a_dict[k])
	return a_dict
