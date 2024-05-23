#!/usr/bin/env bash

# start celery worker
celery -A calliope_app worker -n short-task-worker-$RANDOM -Q short_queue -l info