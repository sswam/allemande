
# let's interrogate an object thoroughly

def autopsy(obj, path=[], seen=None):
	if seen is None:
		seen = set()
	if id(obj) in seen:
		return
	for name in obj.__dict__:  # dir(obj)
		try:
			val = getattr(obj, name)
			if type(val) in (int, str, float, bool, type(None)):
				print(path + [name], val, sep="\t")
			else:
				autopsy(val, path + [name], seen)
		except Exception as e:
			print(path + [name], "", e, sep="\t")
