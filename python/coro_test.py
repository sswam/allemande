#!/usr/bin/env python3

def price_calculator():
    total = 0
    while True:
        item = yield
        if item is None:
            return total
        price = yield f"Price of {item}?"
        total += price

# Using the coroutine
calc = price_calculator()
next(calc)  # Prime the coroutine

try:
    print(calc.send("apple"))
    print(calc.send(1.50))

    print(calc.send("banana"))
    print(calc.send(0.75))

    print(calc.send("orange"))
    print(calc.send(1.25))

    print(calc.send(None))  # Signal the end and get the total
except StopIteration as e:
    print(f"Total price: ${e.value:.2f}")
