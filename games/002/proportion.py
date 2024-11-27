# map scores from 1=good, 7=bad to percentage

# 1    7

# 100	0

while True:
	s = input("score? ")
	s = int(s)

#	p = 25*(s-1)
#	p = -100/6*s + 700/6
	p = -100/6*(s-7)

	print("percentage", p)
