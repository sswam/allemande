#!/bin/bash -eu

# Debian GNU/Linux Installation

# Part 1 of 2

# These install notes are fairly minimal with a few suggested extras.
# You can also consider installing the developer's preferred setup
# instead, see setup-with-extras.txt for that.

# The developer recommends to use Debian.

# You can either step through these scripts, or run them.

# ======== run some things as root {{{ =======================================

user=$USER
host=$HOSTNAME
servers=(ucm.dev pi.ucm.dev)
server0=${servers[0]}
code=$server0:/home/sam/code
fullname=`awk -F: -v user=$user '$1==user {print $5}' /etc/passwd | sed 's/,.*//'`
read -i "$fullname" -p "Your full name: " fullname
sudo chfn -f "$fullname" $USER

read -p "Settings are user=$user, host=$host, servers=$servers, code=$code, okay? " yn
if [ "$yn" != y ]; then
	echo >&2 "Please fix your settings, then re-run $(basename $0)"
	exit 1
fi

# -------- set up sudo with staff group --------------------------------------

sudo sh -c "
cat <<END >/etc/sudoers.d/local
%staff ALL = (ALL) NOPASSWD: ALL
END

sudo adduser $USER staff
"

newgrp staff
