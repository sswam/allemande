#!/bin/bash
# Enable SysRq and trigger an instant hardware reset
. get_root
echo 1 > /proc/sys/kernel/sysrq
echo b > /proc/sys/kernel/sysrq-trigger
