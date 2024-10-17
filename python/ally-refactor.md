# Ally refactor project

We need to apply transforms to our code, either Part 1 and Part 2, or just Part 2 for some code.
Some code might not need changing, either because it already uses the new interfaces, or it doesn't use this code style at all.

## Part 1

Some scripts have @arg or @argh.arg decorators in the main function, and use main.run in the if __name__ == "__main__" code. For these scripts, we need to:
1. Remove the import: from argh import arg, or import argh
2. Change the if __name__ == "__main__" code to main.go(the_main_function, setup_args)
3. Add a setup_args function just above the if __name__ == "__main__" code, like this for example:

def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-n", "--name", help="name to be greeted")
    arg("--ai", action="store_true", help="use AI to respond")
    arg("-m", "--model", help="specify which AI model e.g. claude, emmy, clia, dav")

It should include all the args from the decorators in this new format.

4. If the main function has code like `get, put = main.io()`, remove it, and add args to the function like this:
    get: geput.Get,
    put: geput.Put,

5. Then continue with Part 2.

## Part 2

Some scripts are using an older IO interface, which is indicated by args get: Get or put: Put in their main function.
1. from ally import geput	# on the same line with others: from ally import ...
2. In the main function, declare get and/or put parameters typed like   get: geput.Get,  put: geput.Put
3. If the function uses put, add a line   print = geput.print(put) at the start of the function
4. Replace calls to put with print, e.g. put("foo") becomes print("foo")
5. If the function uses get(all=True), replace this expression with geput.whole(get)
6. If the function uses get without all, add a line  input = getput.input(get)
7. Replace calls to get without all, with input, e.g. get() becomes input()
8. If the main function passes get or put to other functions, better pass input or print instead, and change references in those functions.
