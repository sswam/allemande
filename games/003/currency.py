# change this to convert Farenheit to Celcius,

def c_to_f(c):
	f = c * 9 / 5 + 32
	return f


def f_to_c(f):
	c = (f - 32) * 5 / 9
	return c


while True:
	t = input("Temperature? ")
	unit = t[-1]
	value = float(t[:-1])
	if unit == "C":
		print("Farenheit", c_to_f(value))
	else:
		print("Celcius", f_to_c(value))


