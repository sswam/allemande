#!/bin/sh
git status -s | awk '{print $2}'
