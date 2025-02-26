#!/bin/bash
. get_root
find /var/spool/allemande/ -name '\.*' -prune -o -type d -name 'req-*' -print | xa move-rubbish
find /var/spool/allemande/ -name '\.*' -prune -o -type d -name '*-req-*' -print | xa move-rubbish
