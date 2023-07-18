#!/bin/bash -eu

# Debian GNU/Linux Installation

# Part 2 of 2

# ======== settings ==========================================================

user=$USER
host=$HOSTNAME
servers=(ucm.dev pi.ucm.dev)
server0=${servers[0]}
code=$server0:/home/sam/code
fullname=`awk -F: -v user=$user '$1==user {print $5}' /etc/passwd | sed 's/,.*//'`

read -p "Settings are user=$user, host=$host, servers=${servers[*]}, code=$code, okay? " yn
if [ "$yn" != y ]; then
	echo >&2 "Please fix your settings, then re-run $(basename $0)"
	exit 1
fi

# -------- set up apt sources.list -------------------------------------------

sudo sh -c "
cat <<END >/etc/apt/sources.list
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://deb.debian.org/debian sid main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian bookworm-backports main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian experimental main contrib non-free non-free-firmware
END
"

# -------- set up 99dontbreakdebian for safety with other sources ------------

sudo sh -c "
cat <<END >/etc/apt/preferences.d/99dontbreakdebian
Package: *
Pin: release o=Debian,a=experimental
Pin-Priority: 1

Package: *
Pin: release o=Debian,a=unstable
Pin-Priority: 90

Package: *
Pin: release o=Debian,a=testing
Pin-Priority: 95

Package: *
Pin: release a=focal
Pin-Priority: 70

Package: *
Pin: release o=LP-PPA-deadsnakes
Pin-Priority: 90

Package: *
Pin: origin ppa.launchpad.net
Pin-Priority: 90

Package: *
Pin: release o=Debian,a=stable
Pin-Priority: 990

Package: *
Pin: release o=Debian,a=stable-updates
Pin-Priority: 990
END
"

# -------- allow staff to install programs without sudo ----------------------

cd /usr/local
dirs="bin sbin man man/man1 lib/site_perl"
sudo mkdir -p $dirs
sudo chgrp staff $dirs
sudo chmod g+w $dirs

# -------- install essential tools and upgrade to Debian bookworm ------------

sudo apt-get update
sudo apt-get -y install ssh rsync screen build-essential devscripts python3-dev python3.10-dev neovim
sudo apt-get -y dist-upgrade

# -------- set up ssh --------------------------------------------------------

mkdir -p ~/.ssh
chmod go-rwx ~/.ssh
ssh-keygen -t rsa -b 4096 -C $user@$server0 -f ~/.ssh/id_rsa -N ""
cat ~/.ssh/id_rsa.pub >>~/.ssh/authorized_keys

# -------- copy ssh keys to servers and connect ------------------------------

for server in "${servers[@]}"; do
	ssh-copy-id $server
	ssh -T -f -oServerAliveInterval=15 -oServerAliveCountMax=3 -N $server
	echo "ln -s -f -t ~ ~sam/allemande" | ssh $server
done

# -------- set up git --------------------------------------------------------

git config --global user.email $user@$server0
git config --global user.name "$fullname"
git config --global pull.rebase false 

# -------- clone allemande ---------------------------------------------------

git clone https://github.com/sswam/allemande
# git clone ucm.dev:allemande  # alternative
# git clone git@github.com:sswam/allemande.git  # alternative
cd allemande

# -------- install python3.10-distutils-bogus --------------------------------

sudo apt-get -y install ./debian/python3.10-distutils-bogus_1.0_all.deb

# -------- install allemande dependencies

sudo apt-get -y install `< debian-requirements.txt`
sudo apt-get -y clean
# pip install torch==1.8.1+cpu,torchvision==0.9.1+cpu -f https://download.pytorch.org/whl/torch_stable.html  # if no GPU
# pip install torch==1.8.1+cpu,torchvision==0.9.1+cpu -f https://download.pytorch.org/whl/torch_stable.html  # if AMD GPU
pip install -r requirements.txt
# pip install -r requirements-appserver.txt  # alternative
# - pip install allemande deps
# - install other allemande deps, eg. whisper.cpp
# - test allemande

## Windows suggested

# - remove edge shortcuts
# - chrome
# - firefox
# - misc fixed font
# - terminal use misc fixed
# - windows search -> chrome or firefox

## Debian suggested

# - install ucm-* packages
# - arcs
# - ucm-tools
# - remote access via sshd port forward
# - ~/.vimrc: set mouse=a
# - nvim rc load ~/.vimrc:

mkdir -p ~/.config/nvim

cat <<END >>~/.config/nvim/init.vim
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc
END
