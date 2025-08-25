#!/bin/bash -eu

# IMPORTANT: Do not simply execute the whole file, rather read it and
# copy-paste the commands after confirming that they are good for your system.

# Installation for Debian GNU/Linux

# These install notes are fairly minimal with a few suggested extras.

# The developer recommends to use Debian.

# Some of the commands here are for setting up a fresh server.
# Please consider whether you need to run them or not.

# To run the web service, you need a domain name and two subdomains:
# 'chat' and 'rooms'. The 'chat' subdomain hosts the main user interface.
# The UI includes an iframe to display chat messages, from
# the 'rooms' subdomain. This protects us from JavaScript,
# so we can include untrusted JavaScript in the chat safely.

# This document has four sections:

# 1. Host setup
# 2. User setup
# 3. Allemande toolkit setup
# 4. Ally Chat setup

# You might want to skip some of them!


# ======== 1. HOST SETUP =====================================================

# -------- user and host settings --------------------------------------------

host=$HOSTNAME
email=$USER@$HOSTNAME
fullname=`awk -F: -v user=$USER '$1==user {print $5}' /etc/passwd | sed 's/,.*//'`
read -i "$fullname" -p "Your full name: " fullname
read -i "$email" -p "Your email: " email
sudo chfn -f "$fullname" $USER

read -p "Settings are user=$USER, email=$email, host=$HOSTNAME, okay? " yn
if [ "$yn" != y ]; then
	echo >&2 "Please fix your settings, and try again"
	exit 1
fi

# -------- as root: set up sudo with staff group -----------------------------

read -p "Your username: " user
echo "%staff ALL = (ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers.d/local >/dev/null
adduser $user staff
adduser $user www-data

# Log out and log in again to activate the new groups

# -------- set up apt sources.list; WARNING this overwrites the file ---------

cat <<END | sudo tee /etc/apt/sources.list >/dev/null
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://deb.debian.org/debian sid main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian bookworm-backports main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://ftp.debian.org/debian experimental main contrib non-free non-free-firmware

deb-src http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian sid main contrib non-free non-free-firmware
deb-src http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb-src http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb-src http://ftp.debian.org/debian bookworm-backports main contrib non-free non-free-firmware
deb-src http://ftp.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb-src http://ftp.debian.org/debian experimental main contrib non-free non-free-firmware
END

# -------- set up 00dontbreakdebian for safety with other sources ------------

cat <<END | sudo tee /etc/apt/preferences.d/00dontbreakdebian >/dev/null
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

# -------- allow staff to install programs without sudo (optional) -----------

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


# ======== 2. USER SETUP =====================================================

# -------- set up ssh and generate a key -------------------------------------

mkdir -p ~/.ssh
chmod go-rwx ~/.ssh
ssh-keygen -t rsa -b 4096 -C "$email" -f ~/.ssh/id_rsa -N ""
cat ~/.ssh/id_rsa.pub >>~/.ssh/authorized_keys

# Add your new ssh public key from ~/.ssh/id_rsa.pub to your Github settings:
# https://github.com/settings/keys

# -------- copy ssh public keys to other servers, likely not applicable ------

# for server in ucm.dev pi.ucm.dev; do
# 	ssh-copy-id $server
# 	ssh -T -f -oServerAliveInterval=15 -oServerAliveCountMax=3 -N $server
# done

# -------- set up git --------------------------------------------------------

git config --global user.email "$email"
git config --global user.name "$fullname"
git config --global pull.rebase false      # or true if you prefer!

# -------- nvim settings for vim compatibility -------------------------------
# You can skip this if you don't use nvim or have other preferences

cat <<END >~/.vimrc
set nocp
set hls
END

mkdir -p ~/.config/nvim

cat <<END >>~/.config/nvim/init.vim
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc
END


# ======== 3. ALLEMANDE TOOLKIT SETUP ========================================

# -------- clone allemande ---------------------------------------------------

git clone git@github.com:sswam/allemande.git
# git clone https://github.com/sswam/allemande.git  # alternative, but can't push
# You could also fork on github and clone your version.
sudo ln -sf $PWD/allemande /opt/
cd allemande

# -------- set up a Python 3.13 virtual environment ------------------

sudo apt-get install python3.13-venv python3.13-dev python3.13-tk
python3.13 -m venv venv
. venv/bin/activate

# -------- install Go from upstream ------------------------------------------

go_arch="amd64"  # or just download the right package!
go_url=$(curl https://go.dev/dl/ | sed -n "/href=\"\/dl\/go.*linux-$go_arch/ { s/.*href=\"//; s/\".*//; p; q; }")
rm -f go*.linux-amd64.tar.gz
wget "https://go.dev$go_url"
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go*.linux-amd64.tar.gz
rm go*.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
printf "\n%s\n" 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# Go modules
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

# -------- ai.env: API keys to access AI providers ---------------------------

# The ai.env file does not have to be in ~/my/, that's just where I put it.
mkdir -p ~/my
chmod go-rwx ~/my
cp config/ai.env.dist ~/my/ai.env
# NOTE: edit ~/ai.env and populate as needed with API keys. They are all optional.
# I suggest to make ~/my a git repo, and clone it to your home PC.

# Get API keys from here:

# Hugging Face (dev, free): https://huggingface.co/settings/tokens
# Google (free): https://aistudio.google.com/app/u/2/apikey
# OpenAI: https://platform.openai.com/settings/organization/api-keys
# Anthropic: https://console.anthropic.com/settings/keys
# Perplexity: https://www.perplexity.ai/account/api
# xAI: https://console.x.ai/
# DeepSeek: https://platform.deepseek.com/api_keys
# OpenRouter: https://openrouter.ai/settings/keys
# Venice: https://venice.ai/settings/api
# Serper (search): https://serper.dev/api-key

# -------- bashrc additions --------------------------------------------------

cat <<'END' >>~/.bashrc

set -a
. /opt/allemande/venv/bin/activate
. /opt/allemande/env.sh
. ~/my/ai.env

# Sam's prompt preferences, remove if not wanted!
if [ -n "$PS1" ]; then
	prompt_status() { if [ $? = 0 ]; then echo '# '; else echo -e '#!'; fi; }
	export PS1='$(prompt_status)'
	export PS2='#;'
	stty stop ''
	stty -ixon
fi
END

exec bash  # restart bash

# -------- Build opts-help, opts-long, needed by many scripts (e.g. metadeb) -

(cd bash; make); (cd text; make)
pip install argh
make canon

# -------- install allemande Debian dependencies -----------------------------
# metadeb creates a meta-package, makes it easier to uninstall things later

sudo apt-get install equivs
metadeb -n=allemande-deps debian-allemande-deps.txt

# Alternative without metadeb:
# sudo apt-get -y install $(< debian-packages.txt grep -v '^#')
# sudo apt-get -y clean

# -------- install allemande Python dependencies -----------------------------

pip install -r requirements-core-cpu.txt  # without GPU
# pip install -r requirements-core-cuda.txt  # with NVIDIA GPU
# pip install -r requirements-core-rocm.txt  # with AMD GPU

pip install -r requirements-core.txt
pip install -r requirements-1.txt
# pip install -r requirements-2.txt  # with GPU, there will likely be conflicts / issues!
# pip install -r requirements-cuda.txt  # only if you have an NVIDIA GPU

pip install -e mdformat-light-touch

rm -rf ~/.cache/pip

# -------- build stuff -------------------------------------------------------
# This may likely fail in some way; please check with the developer or fix it!

cd ~/allemande/amps
make

cd ~/allemande
make

# -------- test allemande tools ----------------------------------------------
# llm is the low-level tool, check its --help
# 1sf gives a one-sentence response
# query and process are wrappers
# que and proc give short responses
# 1s and 1w give 1 sentence and 1 word responses
# 1sf and 1wf try to force the model to answer definitively

llm models  # list all supported models and their aliases
query -m=4 "Please tell me a story about ponies!"         # use GPT 4o
1sf 'What is the most famous tower in the world?'         # uses Claude by default
1sf -m=gf 'What is the most famous donkey in the world?'  # use Gemini Flash
fortune | tee /dev/stderr | proc -m=dese "to a poem"      # use Deepseek V3

rm -r ~/llm.log  # remove the llm log files, if you don't want to keep them



# ======== 4. ALLY CHAT SETUP ================================================

# -------- config.js ---------------------------------------------------------

cp config/config.js.dist webchat/static/config.js
# You can edit to set your host URLs.
# The Vapid key is not used yet.

# -------- edit config.sh ----------------------------------------------------

# Edit ~/allemande/config.sh, set your domain name and server name.

# -------- set up secrets.sh -------------------------------------------------

export ALLYCHAT_JWT_SECRET="$(openssl rand -hex 32)"
envsubst < config/secrets.sh.dist > secrets.sh
# Back this up if you are running a production service!

# -------- SSL certificates --------------------------------------------------

# TODO: use LetsEncrypt / certbot

# -------- build nginx with JWT support --------------------------------------

nginx-build-with-jwt "1.22.1-9"  # known good version, compatible with the plugin
# nginx-build-with-jwt           # or try your luck with the latest version, which isn't

# -------- run setup scripts -------------------------------------------------

cd ~/allemande
. ./env.sh

sudo rm -f /etc/nginx/sites-enabled/default
allemande-install
web-install
make canon

# -------- set up firewall for semi-trusted users ----------------------------
# NOTE: This is optional and experimental, you probably should skip it for now.

sudo cp config/remote_user_firewall.conf.dist /etc/remote_user_firewall.conf
# edit /etc/remote_user_firewall.conf to set your gateway at least
# ROUTER_IPv6 can be blank if you don't use IPv6 or want to block it

cat <<END | sudo tee -a /etc/rc.local

/opt/allemande/adm/remote_user_firewall.sh add
/opt/allemande/adm/remote_user_startup.sh
END

sudo chmod +x /etc/rc.local
sudo systemctl enable rc-local

sudo /opt/allemande/adm/remote_user_firewall.sh add

# check that the firewall was applied after reboot, with:
sudo /opt/allemande/adm/remote_user_firewall.sh list

# -------- install other Ally Chat soft dependencies that are tricky ---------

# see requirements-extra.sh: install notes for some other dependencies
