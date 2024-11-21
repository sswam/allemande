#!/bin/bash
eval "$(ally)"
ulimit -n 20000
v time ab -n 100000 -c 10000 "http://localhost:8123/async"
v time ab -n 1000 -c 100 "http://localhost:8123/sync"
v time ab -n 1000 -c 100 "http://localhost:8123/sync_async"
v time ab -n 1000 -c 100 "http://localhost:8123/sync_async_fastapi"
