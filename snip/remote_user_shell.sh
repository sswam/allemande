#!/bin/bash

set -e -u -o pipefail

. /etc/remote_user.conf

exec cgexec -g memory,cpu,pids:"$CGROUP" /bin/bash
