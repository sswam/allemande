Here's an improved version of the `line_finder.md` file with the suggested changes and additional improvements:

```markdown
# Line Finder CLI Tutorial v1.0.1

This tutorial covers how to use the Line Finder CLI tool, which allows you to search for lines in a file or input stream based on various criteria.

## Installation

Ensure you have Python 3 installed on your system. Save the script as `line_finder.py` and make it executable:

```bash
chmod +x line_finder.py
```

## Basic Usage

The basic syntax for using the Line Finder is:

```bash
./line_finder.py [OPTIONS] PATTERN
```

You can pipe input to the script or use it with files:

```bash
cat file.txt | ./line_finder.py PATTERN
```

or

```bash
./line_finder.py PATTERN < file.txt
```

## Options and Features

### 1. Pattern Matching

The `PATTERN` argument is required and specifies the text to search for in each line.

```bash
./line_finder.py "example"
```

### 2. Search Modes

Use the `--mode` option to specify how lines should be matched:

- `all`: Return all matching lines (default)
- `first`: Return only the first matching line
- `last`: Return only the last matching line
- `to_end`: Return all lines from the first match to the end of the file
- `from_start`: Return all lines from the start of the file to the first match
- `last_to_end`: Return all lines from the last match to the end of the file
- `start_to_first`: Return all lines from the start of the file to the first match
- `other`: Return all lines that do not match the pattern (formerly --exclude)

```bash
./line_finder.py --mode first "example"
./line_finder.py --mode to_end "example"
```

### 3. Match Position

Use `--start`, `--end`, or `--whole` to match the pattern at the start, end, or as the entire line:

```bash
./line_finder.py --start "Example"
./line_finder.py --end "example."
./line_finder.py --whole "Exact line match"
```

### 4. Excluding Matched Lines

Use `--exclude` with `to_end`, `from_start`, or `between` modes to exclude the actual matched line(s):

```bash
./line_finder.py --mode to_end --exclude "START" < file.txt
```

### 5. Between Matches

Use `--between` to find lines between the first match of the main pattern and the first occurrence of another pattern:

```bash
./line_finder.py "start" --between "end"
```

### 6. Case Sensitivity

Use `--ignore-case` or `-i` for case-insensitive matching:

```bash
./line_finder.py -i "ExAmPle"
```

### 7. Regular Expressions

Use `--regexp` or `-r` to enable Python regular expression matching:

```bash
./line_finder.py -r "\d{3}-\d{2}-\d{4}"
```

### 8. Wildcard Matching

Use `--wild` or `-w` to enable wildcard matching (* and ?):

```bash
./line_finder.py -w "log*.txt"
```

Note: `--regexp` and `--wild` options are mutually exclusive.

## Examples

1. Find all lines containing "error" (case-insensitive):
   ```bash
   ./line_finder.py -i "error" < logfile.txt
   ```

2. Find the first line starting with "Chapter":
   ```bash
   ./line_finder.py --mode first --start "Chapter" < book.txt
   ```

3. Extract all lines from "Introduction" to "Conclusion", excluding these lines:
   ```bash
   ./line_finder.py "Introduction" --between "Conclusion" --exclude < document.txt
   ```

4. Find all lines not containing "warning":
   ```bash
   ./line_finder.py --mode other "warning" < logfile.txt
   ```

5. Get all lines from the last occurrence of "END" to the end of the file:
   ```bash
   ./line_finder.py --mode last_to_end "END" < data.txt
   ```

6. Find lines matching a regular expression for dates:
   ```bash
   ./line_finder.py -r "\d{4}-\d{2}-\d{2}" < dates.txt
   ```

7. Find files with names matching a wildcard pattern:
   ```bash
   ls | ./line_finder.py -w "*.py"
   ```

## Notes

- The script reads from standard input if no file is specified.
- Output is written to standard output and can be redirected to a file if needed.
- Use quotation marks around patterns containing spaces or special characters.
- The `--regexp` and `--wild` options are mutually exclusive.
- Consider using aliases for longer mode names (e.g., `l2e` for `last_to_end`).
