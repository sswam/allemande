#!/bin/bash
if ! sudo service nginx restart; then
	sudo service nginx status
	echo
	sudo journalctl -xeu nginx.service | tail -n 20
fi
