#!/bin/bash -eu
. opts
remote=$1
branch=$2
confirm=confirm
git fetch $remote $branch
$confirm git reset --hard $branch
