#!/bin/bash
if ! sudo service haproxy restart; then
	sudo service haproxy status
	echo
	sudo journalctl -xeu haproxy.service | tail -n 20
fi
