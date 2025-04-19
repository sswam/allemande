#!/bin/bash -eu
# Kill the automatic1111 stable diffusion webui process,
# if case of failure, so it will restart and hopefully work!
# Depends on our use of /opt/venvs/python3.10-automatic1111
v kill $(psgrep automatic1111 | awk '{print $2}') || true
