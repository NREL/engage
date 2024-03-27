#!/usr/bin/env bash

python3 manage.py loaddata --app template \
      admin_template_type.json \
      admin_template_type_variables.json \
      admin_template_type_techs.json \
      admin_template_type_locs.json \
      admin_template_type_loc_techs.json \
      admin_template_type_loc_tech_params.json \
      admin_template_type_tech_params.json \
      admin_template_type_carriers.json
      
python3 manage.py migrate

python3 manage.py runserver 0.0.0.0:8000