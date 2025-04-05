#!/bin/bash
# sshc.sh: ssh to a remote host and run a command.
remote=$1 ; shift
ssh "$remote" "`printf "%q " "$@"`"
