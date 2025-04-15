#!/usr/bin/env python3

import os
import io
import pytest
from unittest.mock import patch, MagicMock
from typing import Any

import collector_js as subject  # type: ignore

subject_name = subject.__name__

def test_code_collector_init():
    collector = subject.CodeCollectorJS()
    assert collector.selectors == []
    assert collector.scripts == {}
    assert collector.elements == {}

    collector = subject.CodeCollectorJS(['.test', '#main'])
    assert collector.selectors == ['.test', '#main']
    assert collector.scripts == {}
    assert collector.elements == {}

def test_process_empty_content():
    collector = subject.CodeCollectorJS(['.test'])
    collector.process_content('')
    assert collector.scripts == {}
    assert collector.elements == {}

def test_process_simple_script():
    collector = subject.CodeCollectorJS()
    html = '''
    <script>
        function test() { return 42; }
        const x = 1;
        let y = 2;
        var z = 3;
    </script>
    '''
    collector.process_content(html)
    assert 'test' in collector.scripts
    assert 'x' in collector.scripts
    assert 'y' in collector.scripts
    assert 'z' in collector.scripts

def test_process_elements():
    collector = subject.CodeCollectorJS(['.test', '#main'])
    html = '''
    <div class="test">Test 1</div>
    <div id="main">Main content</div>
    <div class="test">Test 2</div>
    '''
    collector.process_content(html)
    assert len(collector.elements) == 3

def test_get_collected_code():
    collector = subject.CodeCollectorJS()
    html = '''
    <script>
        const x = 1;
        let y = 2;
    </script>
    '''
    collector.process_content(html)
    code = collector.get_collected_code(remove_const_let=True)
    assert 'var x = 1' in code
    assert 'var y = 2' in code

    code = collector.get_collected_code(remove_const_let=False)
    assert 'const x = 1' in code
    assert 'let y = 2' in code

@pytest.mark.parametrize("filename,content", [
    ("test.html", "<script>const x = 1;</script>"),
    ("empty.html", ""),
    ("invalid.html", "<not>valid</html>"),
])
def test_process_file(tmp_path, filename, content):
    file_path = tmp_path / filename
    file_path.write_text(content)

    collector = subject.CodeCollectorJS()
    collector.process_file(str(file_path))

    if 'const x = 1' in content:
        assert 'x' in collector.scripts
    else:
        assert collector.scripts == {}

def test_process_file_not_found():
    collector = subject.CodeCollectorJS()
    with pytest.raises(OSError):
        collector.process_file('nonexistent.html')

def test_invalid_javascript():
    collector = subject.CodeCollectorJS()
    html = '''
    <script>
        this is not valid javascript;
    </script>
    '''
    collector.process_content(html)
    assert collector.scripts == {}

@patch('builtins.print')
@patch('builtins.open')
def test_collect_code_main(mock_open, mock_print):
    mock_open.return_value = io.StringIO("<script>const x = 1;</script>")
    files = ['test1.html', 'test2.html']
    selectors = ['.test']
    subject.collect_code(files=files, selectors=selectors, remove_const_let=True)
    mock_print.assert_called_once()

def test_element_key_generation():
    collector = subject.CodeCollectorJS(['.test'])
    html = '''
    <div id="unique">Test</div>
    <div class="test multiple classes">Test</div>
    <div>No identifier</div>
    '''
    collector.process_content(html)

    # Check that different types of elements get different keys
    elements = collector.elements
    assert any('unique' in key for key in elements.keys())
    assert any('test_multiple_classes' in key for key in elements.keys())
    assert any(key.isdigit() or '_' in key for key in elements.keys())

def test_setup_args():
    mock_arg = MagicMock()
    subject.setup_args(mock_arg)

    # Verify all expected arguments are set up
    calls = mock_arg.call_args_list
    assert any('files' in str(call) for call in calls)
    assert any('selector' in str(call) for call in calls)
    assert any('remove-const-let' in str(call) for call in calls)
