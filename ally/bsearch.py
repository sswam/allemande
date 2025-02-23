"""Binary search utilities."""

def find_lowest_int_true(predicate, *, start=0):
	"""Find lowest int where predicate is True.
	Assumes predicate eventually becomes True and stays True."""
	# First find a True value
	num = start
	step = 1
	while not predicate(num):
		num += step
		step *= 2

	# Binary search for lowest True
	low = num - step//2 + 1  # Possible True
	high = num               # Known True
	while low < high:
		mid = (low + high) // 2
		if not predicate(mid):
			low = mid + 1
		else:
			high = mid
	return high
