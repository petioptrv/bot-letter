#! /usr/bin/env bash
set -e

python /app/app/celeryworker_pre_start.py

supervisord -c /app/worker-supervisord.conf
