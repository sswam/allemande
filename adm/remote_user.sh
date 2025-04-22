sudo mkdir /etc/remote_user/{user,group,chroot} -p

# audit
# Find all writable locations in chroot
find /srv/remote_user -type d -writable
# Check mounted filesystems
findmnt | grep remote_user
# List all device nodes
find /srv/remote_user/dev -type c,b
# Verify no setuid binaries
find /srv/remote_user -perm -4000

