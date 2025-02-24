import random


class Shortcode():

	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = "Returns a random number between two values to one decimal place"

	def run_atomic(self, pargs, kwargs, context):
		_min = self.Unprompted.parse_advanced(pargs[0], context)
		_max = self.Unprompted.parse_advanced(pargs[1], context)

		val = random.uniform(float(_min), float(_max))
		val = round(val, 1)

		return val
