awk '
	/^#File: / {
		if (file) close(file)
		file = substr($0, 7)
		next
	}
	{ if (file) print > file }
'
