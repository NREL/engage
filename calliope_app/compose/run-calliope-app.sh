#!/usr/bin/env bash

python3 manage.py migrate

python3 manage.py runserver 0.0.0.0:8000

# fixture, db sample data
python3 manage.py loaddata --app template \
      admin_template_type.json \
      admin_template_type_variables.json \
      admin_template_type_techs.json \
      admin_template_type_locs.json \
      admin_template_type_loc_techs.json \
      admin_template_type_parameters.json