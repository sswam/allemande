#!/bin/bash
cache-prune -q -w -R -f=300M /home/sam/allemande/rooms.extra.cache
/opt/allemande/jobs/5m/local.sh
