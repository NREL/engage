#!/usr/bin/env bash

celery worker -n short-task-worker -A calliope_app -Q short_queue -l info