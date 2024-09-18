from Levenshtein import distance
from collections import deque

class BKTreeNode:
    """
    Represents a node in the BK-tree.

    Attributes:
        word (str): The word stored in this node.
        children (dict): A dictionary mapping distances to child nodes.
    """

    def __init__(self, word: str):
        self.word = word
        self.children = {}

class BKTree:
    """
    Implements a Burkhard-Keller tree for efficient fuzzy string matching.

    The BK-tree allows for quick lookup of words within a specified edit distance.
    """

    def __init__(self):
        self.root = None

    def add(self, word: str) -> None:
        """
        Adds a word to the BK-tree.

        Args:
            word (str): The word to be added to the tree.
        """
        if self.root is None:
            self.root = BKTreeNode(word)
            return

        node = self.root
        while True:
            d = distance(word, node.word)
            if d == 0:  # Word already exists in the tree
                return
            if d not in node.children:
                node.children[d] = BKTreeNode(word)
                return
            node = node.children[d]

    def build_tree(self, words: list[str]) -> None:
        for word in words:
            self.add(word)

    def search(self, word: str, max_distance: int) -> list[tuple[str, int]]:
        """
        Searches for words in the tree within the specified maximum edit distance.

        Args:
            word (str): The word to search for.
            max_distance (int): The maximum edit distance to consider.

        Returns:
            list[tuple[str, int]]: A list of tuples containing matching words and their distances,
                                   sorted by distance.
        """
        if self.root is None:
            return []

        results = []
        queue = deque([(self.root, 0)])

        while queue:
            node, _ = queue.popleft()
            d = distance(word, node.word)

            if d <= max_distance:
                results.append((node.word, d))

            min_distance = max(0, d - max_distance)
            max_distance_child = d + max_distance

            for child_distance in range(min_distance, max_distance_child + 1):
                if child_distance in node.children:
                    queue.append((node.children[child_distance], 0))

        return sorted(results, key=lambda x: x[1])
