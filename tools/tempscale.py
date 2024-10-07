#!/usr/bin/env python3

"""
This module converts temperatures between Celsius, Fahrenheit, and Kelvin.
"""

import sys
from argh import arg
from ally import main

__version__ = "0.1.0"

def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32

def celsius_to_kelvin(celsius: float) -> float:
    return celsius + 273.15

def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9

def fahrenheit_to_kelvin(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9 + 273.15

def kelvin_to_celsius(kelvin: float) -> float:
    return kelvin - 273.15

def kelvin_to_fahrenheit(kelvin: float) -> float:
    return (kelvin - 273.15) * 9 / 5 + 32

def convert_temperature(value: str) -> None:
    try:
        num, unit = value[:-1], value[-1].upper()
        temp = float(num)

        if unit == 'C':
            fahrenheit = celsius_to_fahrenheit(temp)
            kelvin = celsius_to_kelvin(temp)
            print(f"{fahrenheit:.2f}F {kelvin:.2f}K")
        elif unit == 'F':
            celsius = fahrenheit_to_celsius(temp)
            kelvin = fahrenheit_to_kelvin(temp)
            print(f"{celsius:.2f}C {kelvin:.2f}K")
        elif unit == 'K':
            celsius = kelvin_to_celsius(temp)
            fahrenheit = kelvin_to_fahrenheit(temp)
            print(f"{celsius:.2f}C {fahrenheit:.2f}F")
        else:
            raise ValueError("Unknown temperature unit. Supported units: C, F, K.")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)

@arg('temperatures', nargs='+', help="Temperatures to convert, with suffix C/F/K")
def tempscale(
    *temperatures: str
) -> None:
    for temp in temperatures:
        convert_temperature(temp)

if __name__ == "__main__":
    main.run(tempscale)

# This script reads temperature values from command-line arguments, checks the suffix for C, F, or K, and converts the temperature to the other two scales.
