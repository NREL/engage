#!/usr/bin/env bash

# start celery worker
fakemac $(cat /usr/local/xpressmp/bin/xpauth.mac) celery -A calliope_app worker -n long-task-worker-$RANDOM  -Q long_queue -l info
