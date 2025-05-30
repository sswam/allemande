#!/bin/bash -eu

# symlink the allemande home directory to /opt/allemande
# setup the allemande user and portals directory

python_dir="${1:-$(dirname "$(which python)")}"

. get-root

PATH="/usr/sbin:$PATH"

home="$ALLEMANDE_HOME"
user="$ALLEMANDE_USER"
www_user="www-data"
portals="$ALLEMANDE_PORTALS"

if [ ! -d /opt/allemande ]; then
	ln -sfT "$home" /opt/allemande
fi

cp -T "$home/adm/crontab" /etc/cron.d/allemande

groupadd -g "$ALLEMANDE_GID" "$user" || true
groupadd -g "$CHATUSER_GID" "chatuser" || true
useradd -m -d "$portals" -s "$(which bash)" -u "$ALLEMANDE_UID" -g "$ALLEMANDE_GID" "$user" || true

chown $user:$www_user "$portals"
chmod g+rx "$portals"

if [ -z "$(ls "$portals"/.ssh/id_* 2>/dev/null)" ]; then
	sudo -u allemande ssh-keygen
	sudo -u allemande ssh-copy-id ucm.dev
fi

cat <<END >"$portals/.profile"
set -a
. $ALLEMANDE_HOME/env.sh
PATH="$python_dir:\$PATH"
set +a
END

mkdir -p "$portals/.cache"
rm -f "$portals/.cache/whisper"
ln -sfT "$ALLEMANDE_MODELS/whisper" "$portals/.cache/whisper"
chown -R "$user:$www_user" "$portals/.cache"

for module in $ALLEMANDE_MODULES; do
	module_dir="$portals/$module"

	mkdir -p "$module_dir"
	CONFIG="$ALLEMANDE_HOME/config/$module/default.yaml"
	if [ -e "$CONFIG" ]; then
		ln -sfT "$CONFIG" "$module_dir/config.yaml"
	fi

	chown $user:$www_user "$module_dir"
done

"$ALLEMANDE_HOME/canon/allemande-user-add" www-data
"$ALLEMANDE_HOME/canon/allemande-user-add" "$SUDO_USER"

"$ALLEMANDE_HOME/safety/safety_setup.sh"

touch "$portals/gpu_mutex"
chown $user:$www_user "$portals/gpu_mutex"
chmod g+rw "$portals/gpu_mutex"
