#!/bin/bash -eu

# symlink the allemande home directory to /opt/allemande
# setup the allemande user and ports directory

python_dir="${1:-$(dirname "$(which python)")}"

. get_root

home="$ALLEMANDE_HOME"
user="$ALLEMANDE_USER"
ports="$ALLEMANDE_PORTS"

ln -sfT "$home" /opt/allemande

cp -T "$home/adm/crontab" /etc/cron.d/allemande

groupadd -g "$ALLEMANDE_GID" "$user" || true
useradd -m -d "$ports" -s "$(which bash)" -u "$ALLEMANDE_UID" -g "$ALLEMANDE_GID" "$user" || true

chown $user:$user "$ports"
chmod g+rx "$ports"

sudo -u allemande ssh-keygen
sudo -u allemande ssh-copy-id ucm.dev

cat <<END >"$ports/.profile"
set -a
. $ALLEMANDE_HOME/env.sh
PATH="$python_dir:\$PATH"
set +a
END

mkdir -p "$ports/.cache"
rm -f "$ports/.cache/whisper"
ln -sfT "$ALLEMANDE_MODELS/whisper" "$ports/.cache/whisper"
chown -R "$user:$user" "$ports/.cache"

for module in $ALLEMANDE_MODULES; do
	module_dir="$ports/$module"

	mkdir -p "$module_dir"
	CONFIG="$ALLEMANDE_HOME/config/$module/default.yaml"
	if [ -e "$CONFIG" ]; then
		ln -sfT "$CONFIG" "$module_dir/config.yaml"
	fi

	chown $user:$user "$module_dir"
done

"$ALLEMANDE_HOME/adm/allemande-user-add" www-data
"$ALLEMANDE_HOME/adm/allemande-user-add" sam

"$ALLEMANDE_HOME/safety/setup"
