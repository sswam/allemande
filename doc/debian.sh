#!/bin/bash -eu

# Debian GNU/Linux Installation

# These install notes are fairly minimal with a few suggested extras.

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

read -p "Settings are user=$user, host=$host, servers=${servers[*]}, code=$code, okay? " yn
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

# -------- set up 00dontbreakdebian for safety with other sources ------------

sudo sh -c "
cat <<END >/etc/apt/preferences.d/00dontbreakdebian
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
sudo apt-get -y install ssh rsync screen build-essential devscripts python3-dev neovim
sudo apt-get -y dist-upgrade

# -------- configure preferred editor ----------------------------------------

sudo update-alternatives --config editor

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

# -------- clone allemande and use the main branch ---------------------------

git clone https://github.com/sswam/allemande.git
# git clone ucm.dev:allemande  # alternative
# git clone git@github.com:sswam/allemande.git  # alternative
cd allemande

# -------- install python3.11-distutils-bogus --------------------------------

sudo apt-get -y install ./debian/python3.11-distutils-bogus_1.0_all.deb

# -------- set up a Python 3.11 or 3.12 virtual environment ------------------

# NOTE: use 3.11 on stable or 3.12 on testing / sid. Python 3.13 is no good yet.

sudo apt install python3.11-venv python3.11-dev python3.11-tk
python3.11 -m venv venv
# sudo apt install python3.12-venv python3.12-dev python3.12-tk
# python3.12 -m venv venv
. venv/bin/activate

# -------- Build htmlsplit, needed to download Go ----------------------------

(cd html; make)

# -------- setup names for tools, and environment ----------------------------

make canon
. ./env.sh

# -------- install Go from upstream ------------------------------------------

go_url=$(curl https://go.dev/dl/ | htmllinks | grep linux | head -n1)
rm -f go*.linux-amd64.tar.gz
wget "https://go.dev$go_url"
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go*.linux-amd64.tar.gz
rm go*.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
printf "\n%s\n" 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# Go modules
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

# -------- Build opts-help, opts-long, needed by many scripts (e.g. metadeb) -

(cd bash; make); (cd text; make)
make canon

# -------- install allemande Debian dependencies -----------------------------

metadeb -n=allemande-deps debian-allemande-deps.txt

# Alternative without metadeb:
# sudo apt-get -y install `< debian-packages.txt grep -v '^#'`
# sudo apt-get -y clean

# -------- bashrc additions --------------------------------------------------

mkdir -p ~/my
chmod go-rwx ~/my
touch ~/my/ai.env
# NOTE: copy ai.env or populate as needed with API keys
# refer to config/ai.env.dist

cat <<'END' >>~/.bashrc

set -a
. ~/allemande/venv/bin/activate
. ~/allemande/env.sh
. ~/my/ai.env

if [ -n "$PS1" ]; then
	prompt_status() { if [ $? = 0 ]; then echo '# '; else echo -e '#!'; fi; }
	export PS1='$(prompt_status)'
	export PS2='#;'
	stty stop ''
	stty -ixon
fi
END

exec bash

# -------- unprompted --------------------------------------------------------

mkdir -p ~/soft-ai
cd ~/soft-ai
git clone git@github.com:ThereforeGames/unprompted.git
ln -s ~/soft-ai/unprompted ~/allemande/unprompted/unprompted
cd ~/allemande

# -------- build stuff -------------------------------------------------------

make

# -------- install allemande Python dependencies -----------------------------

pip install -r requirements-core.txt
pip install -r requirements-1.txt
pip install -r requirements-2.txt  # there may be issues!

rm -rf ~/.cache/pip

# -------- install whisper.cpp -----------------------------------------------

mkdir -p ~/soft-ai
cd ~/soft-ai
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make -j8

# TODO install scripts so we can run it conveniently

# -------- install clip-interrogator -----------------------------------------

cd ~/soft-ai
git clone https://github.com/pharmapsychotic/BLIP.git
git clone https://github.com/pharmapsychotic/clip-interrogator.git
pip install -e BLIP
pip install -e clip-interrogator

# -------- nvim settings for vim compatibility -------------------------------

touch ~/.vimrc
mkdir -p ~/.config/nvim

cat <<END >>~/.config/nvim/init.vim
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc
END

# -------- copy ai.env secrets file from another staff member ----------------

scp sam@ucm.dev:my/ai.env ~/my/
set -a
. ~/my/ai.env

# -------- run setup scripts -------------------------------------------------

cd ~/allemande
. ./env.sh

allemande-install
web-install
make canon

# -------- test allemande tools ----------------------------------------------

1sf 'What is the most famous tower in the world?'

rm -r ~/llm.log

# -------- set up firewall for semi-trusted chatusers ------------------------

# copy and edit config from adm/remote_user_firewall.sh to /etc/remote_user_firewall.conf

cat <<END | sudo tee -a /etc/rc.local

/opt/allemande/adm/remote_user_firewall.sh add
END

sudo chmod +x /etc/rc.local
sudo systemctl enable rc-local

sudo /opt/allemande/adm/remote_user_firewall.sh add

# check after reboot with:
sudo /opt/allemande/adm/remote_user_firewall.sh list

# -------- TODO: install other allemande deps that are tricky ----------------

#   - stable diffusion / flux
