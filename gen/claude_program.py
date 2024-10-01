# Certainly! Here's a simple Python program that generates a random number between 1 and 100 and asks the user to guess it. The program will provide hints if the guess is too high or too low, and it will keep track of the number of attempts.

import random

# Generate a random number between 1 and 100
secret_number = random.randint(1, 100)

attempts = 0
guess = 0

print("Welcome to the Number Guessing Game!")
print("I'm thinking of a number between 1 and 100.")

while guess != secret_number:
    try:
        guess = int(input("Enter your guess: "))
        attempts += 1

        if guess < secret_number:
            print("Too low! Try again.")
        elif guess > secret_number:
            print("Too high! Try again.")
        else:
            print(f"Congratulations! You guessed the number in {attempts} attempts!")
    except ValueError:
        print("Please enter a valid number.")

print("Thanks for playing!")

# This program does the following:
#
# 1. Imports the `random` module to generate a random number.
# 2. Generates a random number between 1 and 100.
# 3. Initializes variables for tracking attempts and the user's guess.
# 4. Prints a welcome message and instructions.
# 5. Starts a loop that continues until the user guesses the correct number.
# 6. Inside the loop:
#    - Asks the user for their guess.
#    - Increments the attempt counter.
#    - Provides feedback on whether the guess is too high or too low.
#    - Congratulates the user if they guess correctly.
#    - Handles potential errors if the user enters a non-numeric value.
# 7. Prints a closing message when the game ends.
#
# You can copy this code into a Python file (e.g., `guess_number.py`) and run it to play the game.

