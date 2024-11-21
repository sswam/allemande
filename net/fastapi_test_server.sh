#!/bin/bash
eval "$(ally)"
ulimit -n 20000
gunicorn --bind 0.0.0.0:8123 fastapi_test:app --workers 8 --worker-class uvicorn.workers.UvicornWorker --threads 4
