#!/bin/bash -eu
sudo -E --preserve-env=PATH,PYTHONPATH,PERL5LIB "$@"
