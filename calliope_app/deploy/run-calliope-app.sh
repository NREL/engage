#!/usr/bin/env bash

# migrate
python3 manage.py migrate

# fixture, db sample data for api
python3 manage.py loaddata --app api \
    admin_run_parameter.json admin_parameter.json \
    admin_abstract_tech.json admin_abstract_tech_param.json

# fixture, db sample data for template
python3 manage.py loaddata --app template \
      admin_template_type.json \
      admin_template_type_variables.json \
      admin_template_type_techs.json \
      admin_template_type_locs.json \
      admin_template_type_loc_techs.json \
      admin_template_type_loc_tech_params.json \
      admin_template_type_tech_params.json \
      admin_template_type_carriers.json

# collectstatic to /static directory
python3 manage.py collectstatic --no-input

# gunicorn wsgi sever for nginx
gunicorn calliope_app.wsgi:application --bind 0.0.0.0:8888 --timeout 300 --workers 2
