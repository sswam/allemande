#!/bin/bash
rmdir /opt/allemande/.mount_lock
TERM=xterm-256color ssh -tt sam@localhost i allemande make core
