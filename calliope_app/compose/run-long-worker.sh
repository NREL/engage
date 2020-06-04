#!/usr/bin/env bash

celery worker -n long-task-worker -A calliope_app -Q long_queue -l info