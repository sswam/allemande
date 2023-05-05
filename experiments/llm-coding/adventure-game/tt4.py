def main():
	print("Welcome to the Simple Text Adventure Game!")
	print("You wake up in a small room with three doors.")
	print("Do you choose door 1, door 2 or door 3?")

	door = input("> ")

	if door == "1":
		print("You enter door 1 and find a treasure chest.")
		print("Do you open it? (yes or no)")

		choice = input("> ")

		if choice.lower() == "yes":
			print("You open the chest and find gold coins. You win!")
		else:
			print("You decide not to open the chest. You lose!")

	elif door == "2":
		print("You enter door 2 and find a hungry monster.")
		print("Do you fight or run? (fight or run)")

		choice = input("> ")

		if choice.lower() == "fight":
			print("You bravely fight the monster and win. You win!")
		else:
			print("You run away from the monster. You lose!")

	elif door == "3":
		print("You enter door 3 and find a peaceful garden.")
		print("Do you stay or leave? (stay or leave)")

		choice = input("> ")

		if choice.lower() == "stay":
			print("You enjoy your time in the garden. You win!")
		else:
			print("You leave the garden, feeling unsatisfied. You lose!")

	else:
		print("Invalid choice. You are stuck in the room. You lose!")

if __name__ == "__main__":
	main()
