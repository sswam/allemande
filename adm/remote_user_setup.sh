#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

# disable pipewire, etc. for remote users

mkdir -p /etc/systemd/user/{pipewire.service.d,wireplumber.service.d,mpris-proxy.service.d,pipewire-pulse.socket.d,pipewire.socket.d}

COMMON_CONTENT='ExecStartPre=/bin/sh -c '\''! groups "$USER" | grep -q remote'\'''

# Create service drop-ins
for service in pipewire wireplumber mpris-proxy; do
    cat > "/etc/systemd/user/${service}.service.d/50-restrict-group.conf" << EOF
[Service]
${COMMON_CONTENT}
EOF
done

# Create socket drop-ins
for socket in pipewire-pulse pipewire; do
    cat > "/etc/systemd/user/${socket}.socket.d/50-restrict-group.conf" << EOF
[Socket]
${COMMON_CONTENT}
EOF
done

# Reload system daemon configuration
systemctl daemon-reload
