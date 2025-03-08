#!/usr/bin/env python

# I'll help modify i3_bal.py to add the --all and --ALL options, fix issues, and update it based on the requirements. Here's the improved version:

"""i3-bal - Balance the size of windows in i3 containers"""

import argparse
import i3ipc


def balance_container(container) -> None:
    """Balance all child windows in a container"""
    num_children = len(container.nodes)
    if num_children <= 1:
        return

    new_percentage = int(100 / num_children)
    if container.layout == "splith":
        ppt_x = new_percentage
        ppt_y = 0
    elif container.layout == "splitv":
        ppt_x = 0
        ppt_y = new_percentage
    else:
        return

    # Add a loop to iterate multiple times to balance window sizes
    for _ in range(4):
        container.command_children(f"resize set {ppt_x} ppt {ppt_y} ppt")


def balance_up_to_focused(focused) -> None:
    """Balance containers from workspace root down to focused window's parent"""
    # Start from workspace root and work down to focused window's parent
    current = focused.workspace()
    path = []
    node = focused.parent
    while node and node.id != current.id:
        path.append(node)
        node = node.parent

    # Balance from top down
    if current:
        balance_container(current)
    for container in reversed(path):
        balance_container(container)


def balance_entire_tree(root) -> None:
    """Balance every container in the entire tree"""
    # Process current container
    balance_container(root)

    # Recursively process all child containers
    for node in root.nodes:
        balance_entire_tree(node)


def main(argv) -> int:
    """Main program entry point"""
    parser = argparse.ArgumentParser(description="Balance i3 window sizes")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--all", action="store_true",
                    help="Balance from workspace root to focused window's parent")
    group.add_argument("-A", "--ALL", action="store_true",
                    help="Balance entire i3 tree")
    args = parser.parse_args(argv[1:])

    i3 = i3ipc.Connection()
    tree = i3.get_tree()
    focused = tree.find_focused()

    if args.ALL:
        balance_entire_tree(tree)
    elif args.all:
        balance_up_to_focused(focused)
    else:
        if not focused.parent:
            return 0
        balance_container(focused.parent)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
