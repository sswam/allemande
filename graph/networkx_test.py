#!/usr/bin/env python

__version__ = "0.1.0"

def main():
    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.Graph()
    G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4)])

    nx.draw(G, with_labels=True)
    plt.show()

if __name__ == "__main__":
    main()
