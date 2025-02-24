import random


class Shortcode():

	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = "Returns a random number between two values, to a given precision"

	def run_atomic(self, pargs, kwargs, context):
		_min = self.Unprompted.parse_advanced(pargs[0], context)
		_max = self.Unprompted.parse_advanced(pargs[1], context)
		place = self.Unprompted.parse_advanced(pargs[2], context)

		val = random.uniform(float(_min), float(_max))

		if place is not None:
			val = round(val, place)

		return val
