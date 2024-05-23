#!/usr/bin/env bash

celery -A calliope_app flower --port=5555 --persistent=False --basic_auth=$FLOWER_BASIC_AUTH --url-prefix=flower