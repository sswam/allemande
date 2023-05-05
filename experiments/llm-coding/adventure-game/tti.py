def start():
	print("Welcome to the text adventure game!")
	print("You are in a dark forest, thick with towering trees.")
	print("To the north, south, east or west of you, ")
	print("there seems to be a faint path cutting through the undergrowth.")
	choice = None
	
	while choice != 'quit':
		choice = input("Which direction would you like to go? (N, S, E, W, quit) ")
		if choice == 'N' or choice == 'n':
			north()
		elif choice == 'S' or choice == 's':
			south()
		elif choice == 'E' or choice == 'e':
			east()
		elif choice == 'W' or choice == 'w':
			west()
def north():
	print("You head north along the winding path.")
	print("The trees here seem taller and denser than before.")
	print("There are three paths diverging in the mist before you: one heading northwest, northeast or straight ahead.")
	path = input("Which path do you take? (NW, NE, straight ahead) ")
	if path == 'NW' or path == 'nw':
			northwest()
	elif path == 'NE' or path == 'ne':
			northeast()
	else:
			straightahead()
def south():
	print("The path curves southward as the trees thin out a bit.")
	print("After a few minutes of walking, you come across a clearing.")
	print("In the center of the clearing is a large old oak tree.")
	print("There are carvings on the trunk that look ancient.")
	print("What would you like to do? (Examine carvings, Continue walking, quit) ")
	choice = input()
	if choice == 'Examine carvings' or choice == 'examine carvings':
			examinecarvings()
	elif choice == 'Continue walking' or choice == 'continue walking':
			continuewalking()
	else:
			quit()

# Sam finished the code...

def quit():
	print("Thanks for playing!")

if __name__ == "__main__":
	start()
