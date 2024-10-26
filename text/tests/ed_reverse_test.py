import pytest
import sys

import ed_reverse as subject
subject_main = subject.process_script

def test_parse_ed_command():
    assert subject.parse_ed_command("1c") == (1, 1, "c", "")
    assert subject.parse_ed_command("2,5d") == (2, 5, "d", "")
    assert subject.parse_ed_command("2,5s/foo/bar/") == (2, 5, "s/foo/bar/", "")
    with pytest.raises(ValueError):
        subject.parse_ed_command("invalid command")

def test_format_ed_command():
    assert subject.format_ed_command(1, 1, "c", "change line 1\n") == "1c\nchange line 1\n.\n"
    assert subject.format_ed_command(2, 5, "d", "") == "2,5d\n"

def test_process_ed_script():
    content = "1c\nchange line 1\n.\n2d\n5,7a\nadd lines\n.\n"
    commands = subject.process_ed_script(content)
    expected_commands = [
        (1, 1, "c", "change line 1\n"),
        (2, 2, "d", ""),
        (5, 7, "a", "add lines\n")
    ]
    assert commands == expected_commands

def test_check_overlap_no_overlap():
    commands = [
        (5, 7, "a", ""),
        (2, 2, "d", ""),
        (1, 1, "c", "")
    ]
    sorted_commands = sorted(commands, key=lambda x: x[0], reverse=True)
    assert not subject.check_overlap(sorted_commands)

def test_check_overlap_with_overlap():
    overlapping_commands = [
        (4, 6, "d", ""),
        (2, 5, "c", "")
    ]
    sorted_commands = sorted(overlapping_commands, key=lambda x: x[0], reverse=True)
    assert subject.check_overlap(sorted_commands)

def test_process_script(tmp_path):
    input_file = tmp_path / "input.ed"
    input_file.write_text("1c\nhello world\n.\n3d\nw\nq\n")
    output_file = tmp_path / "output.ed"

    with open(input_file, 'r') as istream, open(output_file, 'w') as ostream:
        subject_main(istream, ostream, pure=True)

    expected_output = "3d\n1c\nhello world\n.\n"
    assert output_file.read_text() == expected_output

def test_process_script_stdout(capsys, tmp_path):
    input_file = tmp_path / "input.ed"
    input_file.write_text("1c\nhello world\n.\n3d\n")

    with open(input_file, 'r') as istream:
        subject_main(istream, sys.stdout)

    captured = capsys.readouterr()
    expected_output = "3d\n1c\nhello world\n.\nw\nq\n"
    assert captured.out == expected_output
