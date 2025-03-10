#!/bin/bash -eu

trap "git branch" EXIT INT

set -o pipefail

PULL="git pull --commit --no-edit"
MERGE="git merge --no-edit"
PUSH="git push"
CO="git checkout"

cd "$ALLEMANDE_HOME"

$CO main

$PULL sam@ucm.dev:allemande main
$PULL sam@pi.ucm.dev:allemande main
$PULL $ALLEMANDE_GITHUB main
$PULL $BARBARELLA_GITHUB main

#if [ -n "`git-ls-untracked`" -o -n "`git-ls-unstaged`" -o -n "`git-ls-staged`" ]; then
#	messy -n || true
#fi

$PUSH sam@ucm.dev:allemande main
$PUSH sam@pi.ucm.dev:allemande main
$PUSH $ALLEMANDE_GITHUB main
$PUSH $BARBARELLA_GITHUB main

git pull

#$CO allemande
##$PULL sam@ucm.dev:allemande allemande
##$PULL sam@pi.ucm.dev:allemande allemande
##$PUSH sam@ucm.dev:allemande allemande
##$PUSH sam@pi.ucm.dev:allemande allemande
#$PULL $ALLEMANDE_GITHUB allemande
#$MERGE main
#$PUSH $ALLEMANDE_GITHUB allemande
#$PULL $ALLEMANDE_GITHUB allemande
#
#$CO barbarella
#$PULL $BARBARELLA_GITHUB barbarella
#$MERGE main
#$PUSH $BARBARELLA_GITHUB barbarella
#$PULL $BARBARELLA_GITHUB barbarella
#
#$CO main
