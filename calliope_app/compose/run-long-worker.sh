#!/usr/bin/env bash

celery -A calliope_app worker -n long-task-worker -Q long_queue -l info