import json
import inspect

def get_args_as_json():
	frame = inspect.currentframe().f_back
	args = inspect.getargvalues(frame)
	arg_dict = {arg: args.locals[arg] for arg in args.args}
	return json.dumps(arg_dict, default=str, indent=2)

def test(a, b):
	print(get_args_as_json())

test(1, "foo")
