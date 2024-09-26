import pytest
import os
import tempfile
import subprocess
from pathlib import Path
from stamp import extract_metadata, insert_metadata, erase_metadata, convert_image

@pytest.fixture
def temp_dir():
	with tempfile.TemporaryDirectory() as tmpdirname:
		yield Path(tmpdirname)

@pytest.fixture
def test_jpg(temp_dir):
	test_jpg = temp_dir / "test.jpg"
	subprocess.run(["convert", "-size", "100x100", "xc:white", str(test_jpg)], check=True)
	return test_jpg

@pytest.fixture
def test_png(temp_dir):
	test_png = temp_dir / "test.png"
	subprocess.run(["convert", "-size", "100x100", "xc:white", str(test_png)], check=True)
	return test_png

@pytest.fixture
def test_metadata(temp_dir):
	test_metadata = temp_dir / "metadata.txt"
	test_metadata.write_text("Test metadata")
	return test_metadata

def test_extract_metadata_jpg_empty(test_jpg):
	assert extract_metadata(test_jpg) == ""

def test_extract_metadata_png_empty(test_png):
	assert extract_metadata(test_png) == ""

def test_insert_metadata_jpg(test_jpg, test_metadata):
	insert_metadata(test_jpg, test_metadata.read_text(), test_jpg)
	assert extract_metadata(test_jpg) == "Test metadata"

def test_insert_metadata_png(test_png, test_metadata):
	insert_metadata(test_png, test_metadata.read_text(), test_png)
	assert extract_metadata(test_png) == "Test metadata"

def test_erase_metadata_jpg(test_jpg, test_metadata):
	insert_metadata(test_jpg, test_metadata.read_text(), test_jpg)
	erase_metadata(test_jpg, test_jpg)
	assert extract_metadata(test_jpg) == ""

def test_erase_metadata_png(test_png, test_metadata):
	insert_metadata(test_png, test_metadata.read_text(), test_png)
	erase_metadata(test_png, test_png)
	assert extract_metadata(test_png) == ""

def test_copy_metadata_jpg_to_png(test_jpg, test_png, test_metadata):
	insert_metadata(test_jpg, test_metadata.read_text(), test_jpg)
	metadata = extract_metadata(test_jpg)
	insert_metadata(test_png, metadata, test_png)
	assert extract_metadata(test_png) == "Test metadata"

def test_copy_metadata_png_to_jpg(test_png, test_jpg, test_metadata):
	insert_metadata(test_png, test_metadata.read_text(), test_png)
	metadata = extract_metadata(test_png)
	insert_metadata(test_jpg, metadata, test_jpg)
	assert extract_metadata(test_jpg) == "Test metadata"

def test_convert_jpg_to_png_with_metadata(temp_dir, test_jpg, test_metadata):
	insert_metadata(test_jpg, test_metadata.read_text(), test_jpg)
	converted_png = temp_dir / "converted.png"
	convert_image(test_jpg, converted_png)
	assert extract_metadata(converted_png) == "Test metadata"

def test_convert_png_to_jpg_with_metadata(temp_dir, test_png, test_metadata):
	insert_metadata(test_png, test_metadata.read_text(), test_png)
	converted_jpg = temp_dir / "converted.jpg"
	convert_image(test_png, converted_jpg)
	assert extract_metadata(converted_jpg) == "Test metadata"
