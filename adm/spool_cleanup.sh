#!/bin/bash
. get_root
find /var/spool/allemande/ -name '\.*' -prune -o -type d -name 'req-*' -print | xa rm -rf
find /var/spool/allemande/ -name '\.*' -prune -o -type d -name '*-req-*' -print | xa rm -rf
