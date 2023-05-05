choice = input("You awake one morning in a dense, misty forest. Do you go left towards a deep, dark cave or right towards a twisting mountain path? Type 'left' or 'right': ")

if choice == 'left':
	choice = input("You enter the cave. Do you venture left, deeper into the darkness or right into a passage lit by a dim blue glow? Type 'left' or 'right': ")
	if choice == 'left':
		print("You stumble in the dark and fall into a deep pit! Game over!")
	elif choice == 'right':
		print("You find a chest of gold coins! You win!")
elif choice == 'right':
	choice = input("You start climbing the mountain path. Partway up, the path forks. Do you go left towards a rickety rope bridge or right up a steep, rocky trail? Type 'left' or 'right': ")
	if choice == 'left':
		print("You carefully cross the bridge but then slip at the far end and tumble into the gorge below! Game over!")
	elif choice == 'right':
		print("You reach the peak of the mountain to find a wise old hermit who shares with you the secret to happiness. You win!")
else:
	print("I don't understand that choice. Game over!")
