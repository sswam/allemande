#!/bin/bash -eu
(dunstctl set-paused true; sleep ${1:-600}; dunstctl set-paused false) &
