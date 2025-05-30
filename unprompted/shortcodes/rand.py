import random


class Shortcode():

	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = "Returns a random number between two values, to a given precision"

	def run_atomic(self, pargs, kwargs, context):
		_min = self.Unprompted.parse_advanced(pargs[0], context)
		_max = self.Unprompted.parse_advanced(pargs[1], context)
		places = self.Unprompted.parse_advanced(pargs[2], context) if len(pargs) > 2 else 0

		val = random.uniform(float(_min), float(_max))

		if places == 0:
			val = int(val)
		elif places != "":
			val = round(val - (10**-places)/2, int(places))
		if val == 0:
			val = 0

		return val
