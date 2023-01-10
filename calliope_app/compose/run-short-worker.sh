#!/usr/bin/env bash

celery -A calliope_app worker -n short-task-worker -Q short_queue -l info