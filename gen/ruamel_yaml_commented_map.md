To extract comments from a ruamel.yaml CommentedMap, you must access its internal Comment Attribute (ca). Because comments in YAML are not part of the standard data structure, they are stored in this metadata object, which indexes them relative to keys or document positions.

1. Extracting Key-Specific Comments
For comments associated with a specific key (e.g., inline comments), use the ca.items dictionary.
Syntax: map_object.ca.items[key]
Structure: This returns a list (usually with 4 indices) containing CommentToken objects:
Index 2: End-of-line (inline) comment 
Index 3: Comments on lines following the key 

# Example for a key 'a'
comment_tokens = loaded_map.ca.items['a']
if comment_tokens[2]:
    print(comment_tokens[2].value)  # Extract the text value

2. Extracting Top-Level or Document Comments
Comments that appear at the very beginning of a file or before a mapping are stored at the root of the ca attribute.
Top/Header Comments: map_object.ca.comment[1] typically contains a list of tokens for comments preceding the map.
Bottom/Final Comments: map_object.ca.end may contain comments found at the end of the document structure.
3. Utility Function to Extract All Comments

Since comments are stored in nested lists of CommentToken objects, you can use a helper to clean the data:
python:

def get_key_comments(commented_map, key):
    tokens = commented_map.ca.items.get(key, [])
    comments = []
    for item in tokens:
        if item is None:
            continue
        if isinstance(item, list):
            comments.extend([t.value for t in item if t])
        else:
            comments.append(item.value)
    return comments
