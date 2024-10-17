import tempfile
import os
from io import StringIO
from unittest.mock import patch
import pytest
from func_replace import func_replace, process_file


NEW_FUNCTION_CONTENT = '''
def original_function():
	print("This is the new function")
'''

NEW_METHOD_CONTENT = '''
class OriginalClass:
	def original_method(self):
		print("This is the new method")
'''

# Constants for test_add_new_function
NEW_FUNCTION_TO_ADD = '''
def new_function():
	print("This is a new function")
'''

# Constants for test_process_file
NEW_ITEMS = {
	'original_function': 'def original_function():\n    print("Replaced function")',
	'OriginalClass': 'class OriginalClass:\n    def original_method(self):\n        print("Replaced method")',
	'new_function': 'def new_function():\n    print("New function")'
}


@pytest.fixture
def test_file():
	temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False)
	temp_file.write('''
def original_function():
	print("This is the original function")

class OriginalClass:
	def original_method(self):
		print("This is the original method")

if __name__ == '__main__':
	original_function()
	OriginalClass().original_method()
''')
	temp_file.close()
	yield temp_file.name
	os.unlink(temp_file.name)

@pytest.mark.parametrize("input_content, expected_in, expected_not_in", [
	(NEW_FUNCTION_CONTENT, "This is the new function", "This is the original function"),
	(NEW_METHOD_CONTENT, "This is the new method", "This is the original method")
])
def test_replace(test_file, input_content, expected_in, expected_not_in):
	with patch('sys.stdin', new=StringIO(input_content)):
		func_replace(test_file)

	with open(test_file, 'r') as f:
		content = f.read()

	assert expected_in in content
	assert expected_not_in not in content

def test_add_new_function(test_file):
	with patch('sys.stdin', new=StringIO(NEW_FUNCTION_TO_ADD)):
		func_replace(test_file, add=True)

	with open(test_file, 'r') as f:
		content = f.read()

	assert "def new_function():" in content
	assert "This is a new function" in content

def test_process_file(test_file):
	process_file(test_file, NEW_ITEMS, add_option=True)

	with open(test_file, 'r') as f:
		content = f.read()

	assert "Replaced function" in content
	assert "Replaced method" in content
	assert "New function" in content
	assert "This is the original function" not in content
	assert "This is the original method" not in content
