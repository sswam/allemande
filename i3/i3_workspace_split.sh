#!/bin/bash -eu
# i3-workspace-split: split the current workspace vertically or horizontally
which=${1:-v}
i3-focus-workspace
i3-msg split $which
