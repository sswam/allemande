import os
import io
import yaml
import json
from pathlib import Path
from functools import partial

import pandas as pd
from PIL import Image
import soundfile
import beautifulsoup4 as bs4
from collections import ChainMap
from collections.abc import MutableMapping


class WrappedIOStream():
	def __init__(self, file=None, stream=None, binary=False, encoding="utf-8"):
		if file is not None and stream is None:
			stream = io.open(file, "rb" if binary else "r", encoding=encoding)
		elif file is None and stream is not None:
			pass
		else:
			raise ValueError("Either file or stream must be specified.")
		if isinstance(stream, io.BufferedIOBase) and not binary:
			stream = io.TextIOWrapper(stream, encoding=encoding)
		elif isinstance(stream, io.TextIOBase) and binary:
			stream = stream.buffer
		self.stream = stream
		self.encoding = encoding
		self.binary = binary

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	def __str__(self):
		data = self.stream.read()
		if isinstance(data, bytes):
			data = data.decode(self.encoding)
		return data

	def __bytes__(self):
		data = self.stream.read()
		if isinstance(data, str):
			data = data.encode(self.encoding)
		return data

	def __iter__(self):
		return self

	def __next__(self):
		data = stream.next()
		if self.binary:
			return data


#	def __next__(self):
#		if self.binary:
#			chunk_size = 4096  # Customize the chunk size as needed
#			chunk = self.stream.read(chunk_size)
#			if not chunk:
#				raise StopIteration
#			return chunk
#		else:
#			return self.readline()

	def __getattr__(self, name):
		return getattr(self.stream, name)

	def close(self):
		if self.stream:
			self.stream.close()
			self.stream = None

	def readline(self):
		return self.stream.readline()

	def write(self, data):
		if isinstance(data, str):
			data = data.encode(self.encoding)
		if isinstance(data, bytes):
			return self.stream.write(data)
		else:
			for chunk in data:
				self.write(chunk)

image_file_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
audio_file_extensions = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".wma"}
text_file_extensions = {".txt", ".md"}
bytes_file_extensions = {".bin", ".dat", ""}

# TODO json lines

def read_text(f):
	return WrappedIOStream(f)
def read_bytes(f):
	return WrappedIOStream(f)
def read_csv(f, sep=","):
	return pd.read_csv(f)
read_tsv = partial(read_csv, sep="\t")
def read_image(f):
	return Image.open(f)  # .convert("RGB")
def read_audio(f):
	return soundfile.read(f)
def read_json(f):
	return json.loads(f.read_text())
def read_jsonl(f):
	return [json.loads(line) for line in f.read_text().splitlines()]
def read_yaml(f):
	return yaml.safe_load(f.read_text())
def read_html(f):
	return bs4.BeautifulSoup(f.read_text(), "html.parser")
def read_xml(f):
	return bs4.BeautifulSoup(f.read_text(), "xml")

def write_text(f, data):
	return f.write_text(data)
def write_bytes(f, data):
	return f.write_bytes(data)
def write_csv(f, data, sep=","):
	return data.to_csv(f, sep=sep)
write_tsv = partial(write_csv, sep="\t")
def write_image(f, data):
	return data.save(f)
def write_audio(f, data):
	return soundfile.write(f, data[0], data[1])
def write_json(f, data):
	return f.write_text(json.dumps(data, indent=4))
def write_jsonl(f, data):
	for d in data:
		f.write_text(json.dumps(d) + "\n")
def write_yaml(f, data):
	return f.write_text(yaml.safe_dump(data))
def write_html(f, data):
	return f.write_text(data.prettify())
def write_xml(f, data):
	return f.write_text(data.prettify())

readers = {
	".csv": read_csv,
	".tsv": read_tsv,
	".json": read_json,
	".jsonl": read_jsonl,
	".yaml": read_yaml,
	".html": read_html,
	".xml": read_xml,
}

writers = {
	".csv": write_csv,
	".tsv": write_tsv,
	".json": write_json,
	".jsonl": write_jsonl,
	".yaml": write_yaml,
	".html": write_html,
	".xml": write_xml,
}

def setup_readers_and_writers():
	for ext in text_file_extensions:
		readers[ext] = read_text
		writers[ext] = write_text
	for ext in bytes_file_extensions:
		readers[ext] = read_bytes
		writers[ext] = write_bytes
	for ext in image_file_extensions:
		readers[ext] = read_image
		writers[ext] = write_image
	for ext in audio_file_extensions:
		readers[ext] = read_audio
		writers[ext] = write_audio

setup_readers_and_writers()

def read(path):
	ext = Path(path).suffix
	reader = readers.get(ext)
	if reader is None:
		raise ValueError(f"Unknown file extension: {ext}")
	return reader(path)

def write(path, data):
	ext = Path(path).suffix
	writer = writers.get(ext)
	if writer is None:
		raise ValueError(f"Unknown file extension: {ext}")
	return writer(path, data)

class DirectoryDict(MutableMapping):
	""" A dict-like object that stores its data in a directory. """

	def __init__(self, directory, read=read, write=write, subdirs=False):
		self.directory = directory
		self.subdirs = subdirs
		self.read = read
		self.write = write
		if not os.path.exists(directory):
			os.makedirs(directory)

	def _filepath(self, key):
		return os.path.join(self.directory, key)

	def __getitem__(self, key):
		path = self._filepath(key)
		try:
			if not os.path.isdir(path):
				return self.read(path)
			if self.subdirs:
				return DirectoryDict(path, subdirs=True)
			else:
				raise KeyError(key)
		except FileNotFoundError:
			raise KeyError(key)

	def __setitem__(self, key, value):
		path = self._filepath(key)
		if os.path.isdir(path):
			raise KeyError("Cannot overwrite a directory")
		self.write(path, value)

	def __delitem__(self, key):
		path = self._filepath(key)
		if os.path.isdir(path):
			raise KeyError("Cannot delete a directory")
		try:
			os.remove(path)
		except FileNotFoundError:
			raise KeyError(key)

	def __contains__(self, key):
		path = self._filepath(key)
		return os.path.exists(path)

	def __iter__(self):
		filenames = sorted(os.listdir(self.directory))
		if not self.subdirs:
			filenames = filter(lambda f: not os.path.isdir(self._filepath(f)), filenames)
		return iter(filenames)


