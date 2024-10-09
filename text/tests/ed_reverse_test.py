import io
import pytest

import ed_reverse as subject
subject_main = subject.process_script

def test_parse_ed_command():
    assert subject.parse_ed_command('1c') == (1, 1, 'c')
    assert subject.parse_ed_command('2,5d') == (2, 5, 'd')
    with pytest.raises(ValueError):
        subject.parse_ed_command('invalid command')

def test_format_ed_command():
    assert subject.format_ed_command(1, 1, 'c') == '1c'
    assert subject.format_ed_command(2, 5, 'd') == '2,5d'

def test_process_ed_script():
    content = '1c\nchange line 1\n.\n2d\n5,7a\nadd lines\n.\n'
    commands = subject.process_ed_script(content)
    expected_commands = [
        (1, 1, 'c', 'change line 1'),
        (2, 2, 'd', ''),
        (5, 7, 'a', 'add lines')
    ]
    assert commands == expected_commands

def test_check_overlap_no_overlap():
    commands = [
        (5, 7, 'a', ''),
        (2, 2, 'd', ''),
        (1, 1, 'c', '')
    ]
    sorted_commands = sorted(commands, key=lambda x: x[0], reverse=True)
    assert not subject.check_overlap(sorted_commands)

def test_check_overlap_with_overlap():
    overlapping_commands = [
        (2, 5, 'c', ''),
        (4, 6, 'd', '')
    ]
    sorted_commands = sorted(overlapping_commands, key=lambda x: x[0], reverse=True)
    with pytest.raises(SystemExit):
        subject.check_overlap(sorted_commands)

def test_process_script():
    input_script = '1c\nhello world\n.\n3d\n'
    expected_output = '3d\n\n1c\nhello world\n.\n'
    input_stream = io.StringIO(input_script)
    output_stream = io.StringIO()
    subject_main(istream=input_stream, ostream=output_stream)
    output = output_stream.getvalue()
    assert output.strip() == expected_output.strip()
