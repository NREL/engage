#!/usr/bin/env bash

python3 manage.py migrate

# Seeds reference data only into an empty database -- see the script for why
# loading these fixtures unconditionally is dangerous.
compose/seed-reference-data.sh

python3 manage.py runserver 0.0.0.0:8000