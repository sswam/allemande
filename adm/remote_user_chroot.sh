#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

chroot=${1:-$CHROOT_BASE}

# mount points
mkdir -p "$chroot"/{usr,dev/pts,proc,sys,tmp,home,etc/ssl,run,/var/lib,/var/log,/var/run,/var/tmp,/var/cache}

# copy device nodes
cd /dev
for device in null zero urandom tty console nvidia*; do
	if [ ! -e "$device" ]; then
		continue
	fi
	cp -a -T "$device" "$chroot/dev/$device"
done

cd "$chroot"

# tmp permissions
chmod a+rwxt tmp var/tmp

# resolv.conf
(
	for ns in $NAMESERVERS; do
		echo "nameserver $ns"
	done
) >> etc/resolv.conf

# hosts
cat << EOF >> etc/hosts
127.0.0.1       localhost
EOF

# essential /etc files
for entry in alternatives profile bash.bashrc remote_user.conf ca-certificates.conf ssl/certs ssl/openssl.cnf dictionaries-common; do
	cp -a -T "/etc/$entry" "$chroot/etc/$entry"
done

# passwd and group files
for file in passwd group shadow gshadow; do
	if [ ! -e "$file" ]; then
		touch "etc/$file"
	fi
done
chown root:shadow etc/shadow etc/gshadow
chmod 640 etc/shadow etc/gshadow

grep -e "^root:" /etc/passwd > "$chroot/etc/passwd"
grep -e "^root:" /etc/shadow > "$chroot/etc/shadow"
grep -e "^root:" -e "^$REMOTE_GROUP:" /etc/group > "$chroot/etc/group"
grep -e "^root:" -e "^$REMOTE_GROUP:" /etc/gshadow > "$chroot/etc/gshadow"

# symlinks to usr
for dir in bin lib lib32 lib64 libx32 sbin; do
	ln -sfT usr/$dir $dir
done

# copy remote user shell
# see: snip/remote_user_shell.sh
# cp "$ALLEMANDE_HOME/canon/remote-user-shell" /usr/local/bin/

# add chroot mounts to system /etc/fstab
if ! fgrep -q "# mounts for chroot $chroot" /etc/fstab; then
	cat << EOF >> /etc/fstab
# mounts for chroot $chroot
/usr      $chroot/usr            none      bind,ro,nosuid                  0 0
proc      $chroot/proc           proc      defaults,hidepid=2,gid=staff    0 0
sysfs     $chroot/sys            sysfs     nosuid,noexec,nodev             0 0
cgroup2   $chroot/sys/fs/cgroup  cgroup2   ro,nosuid,nodev,noexec,relatime 0 0
devpts    $chroot/dev/pts        devpts    nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000    0 0
EOF
fi

systemctl daemon-reload
