# this html module is in the public domain
# Sam Watkins, 2012

from l import *

def split(raw_html):
	html = raw_html.replace('\r', '')
	html = raw_html.replace('&nbsp;', ' ')
	lines = re.findall(r'<.*?>\s*|[^<]+', html)
	lines = [re.sub(r'^\s+|\s+$', '', l) for l in lines]
	return lines

def parse_lines(lines, do_expand_singles=True):
	parsed = [parse_line(l) for l in lines]
	if do_expand_singles:
		parsed = expand_singles(parsed)
	return parsed

def parse_line(l):
	text = tag = open = close = attrs = None
	is_tag = re.match(r'^<', l)
	if is_tag:
		close = bool(re.match(r'^</', l))
		open = not close
		if re.search(r'/>$', l):
			close = True
		(tag, attrs) = re.search(r'([^<>/\s]+)(.*?)/?>$', l).groups()
	else:
		text = l  # disentify? squeeze spaces? maybe not yet
	return (text, tag, open, close, attrs, l)

def expand_singles(parsed_lines):
	out = []
	for p in parsed_lines:
		(text, tag, open, close, attrs, raw) = p
		if open and close:
			out.append((text, tag, True, False, attrs, raw))
			out.append((text, tag, False, True, None, ''))  # hmmm...!
		else:
			out.append((text, tag, open, close, attrs, raw))
	return out

def tidy_html_text(t):
	t = re.sub(r'^\s+|\s+$', '', t)
	t = re.sub(r'\s+', ' ', t)
	return t

def extract_table_data(parsed, with_th=True, tidy_values=True, keep_tags=None):
	# This does not preseve tags within table cells,
	# for now I don't need them.

	keep_tags = keep_tags or []
	rows = []
	row = None
	value = None
	value_type = None
	colspan = None

	# this is 'event driven', not ideal
	for p in parsed:
		(text, tag, start, end, attrs, raw) = p
#		print raw
#		print "  ", text, tag, start, end, repr(attrs)
		tr = tag == 'tr'
		td = tag == 'td'
		th = tag == 'th'
		cell = td or th
		ctl = tr or cell
		if tag in keep_tags:
			if value != '':
				value += ' '
			value += raw
		if text is not None and value_type:
			if value == '':
				value = text
			else:
				value += " " + text
		if ctl and value is not None:
			if value_type == 'td' or (value_type == 'th' and with_th):
				if tidy_values:
					value = tidy_html_text(value)
				row.append(value)
				while colspan > 1:
					row.append('')
					colspan -= 1
			value = None
			value_type = None
			colspan = None
		if start and cell:
			value = ""
			value_type = tag  # td or th
			colspan = 1
			match = re.search(r'colspan=["\']?(\d+)', attrs)
			  # not quite right!
			if match:
				colspan = int(match.group(1))
		if tr:
			if row is not None:
				rows.append(row)
			if start:
				row = []
			if end:
				row = None

	return rows

def parse_tables(html, need_th=True, with_th=True, tidy_values=True, keep_tags=None):
	lines = split(html)
	parsed = parse_lines(lines)
	# print(json.dumps(parsed, indent=4))

	has_th = None

	raw_tables = []
	# get all tables without other tables in them
	# This is kind of bad, being 'event driven', rather that procedural.
	for i in range(0, len(parsed)):
		(text, tag, start, end, attr, raw) = p = parsed[i]
		if tag == 'table' and start:
			table_start = i
			has_th = 0
		if tag == 'th' and table_start is not None:
			has_th = 1
		if tag == 'table' and end and table_start is not None:
			table_end = i
			if not need_th or has_th:
				table = parsed[table_start:table_end+1]
				raw_tables.append(table)
			table_start = None
			has_th = None

	data = [extract_table_data(t, with_th=with_th, tidy_values=tidy_values, keep_tags=keep_tags) for t in raw_tables]

	return data, raw_tables
