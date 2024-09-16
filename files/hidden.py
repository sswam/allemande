import os

def contains_hidden_component(path):
    # Split the path into its components
    components = path.split(os.sep)
    
    for component in components:
        # Check if the component starts with a dot
        if component.startswith('.'):
            # Exclude "." and ".." as they're not considered hidden
            if component not in ['.', '..']:
                return True
    
    return False

def test_contains_hidden_component():
    # Test cases
    # TODO not a real pytest test yet
    paths_to_test = [
        "foo/.bar/baz",
        "foo/bar/baz",
        "foo/.bar/.baz",
        "foo/./bar/../baz",
        ".foo/bar/baz",
        "foo/.../bar",
        "foo/..bar/baz",
        ".../foo/bar",
        "foo/bar/.baz/qux",
        ".",
        "..",
        "../foo/bar",
        "foo/bar/..",
    ]
    
    for path in paths_to_test:
        result = contains_hidden_component(path)
        print(f"Path: {path}")
        print(f"Contains hidden component: {result}")
        print()
