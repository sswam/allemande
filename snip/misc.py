

def dict_to_namespace(d):
	""" Convert a dict to an argparse namespace. """
	ns = argparse.Namespace()
	for k, v in d.items():
		setattr(ns, k, v)
	return ns

