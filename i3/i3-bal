#!/usr/bin/env python
# i3-bal - Balance the size of the windows in the current container

import i3ipc

def main(args):
    i3 = i3ipc.Connection()
    tree = i3.get_tree()

    focused = i3.get_tree().find_focused().parent

    num_children = len(focused.nodes)
    if num_children <= 1:
        print('{} children, doing nothing'.format(num_children))
        return 0

    new_percentage = int(100 / num_children)
    if focused.layout == 'splith':
        ppt_x = new_percentage
        ppt_y = 0
    elif focused.layout == 'splitv':
        ppt_x = 0
        ppt_y = new_percentage
    else:
        print('Can\'t resize with {} layout'.format(focused.layout))
        return 1

    # Add a loop to iterate multiple times to balance window sizes
    for _ in range(4):
        focused.command_children('resize set {ppt_x} ppt {ppt_y} ppt'.format(ppt_x=ppt_x, ppt_y=ppt_y))

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
