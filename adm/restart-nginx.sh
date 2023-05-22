#!/bin/bash
if ! sudo systemctl restart nginx; then
	sudo systemctl status nginx
	echo
	sudo journalctl -xeu nginx.service | tail -n 20
fi
