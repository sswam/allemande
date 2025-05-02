# Setup for remote users

## procfs hidepid

Add to /etc/fstab:

```
proc    /proc    proc    defaults,hidepid=2,gid=staff    0    0
```

```sh
sudo mount -o remount /proc
sudo systemctl daemon-reload
```

## set up group

```sh
addgroup remote --gid 779
```

## create chroot

```sh
adm/remote_user_chroot.sh
```

## chroot on ssh login

```sh
. /etc/remote_user.conf
cat << EOF | sudo tee -a /etc/ssh/sshd_config

Match Group $REMOTE_GROUP
  ChrootDirectory $CHROOT_BASE
EOF

sudo systemctl reload ssh
```
