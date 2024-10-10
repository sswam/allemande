#!/bin/bash
. get_root
exec nsenter --target 1 --net
