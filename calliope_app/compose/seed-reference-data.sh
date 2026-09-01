#!/usr/bin/env bash
#
# Seed Engage's reference data -- abstract technologies, parameters, run
# parameters and model templates -- but ONLY into a database that doesn't
# already have it.
#
# WHY THE CHECK MATTERS
#
# These fixtures carry hardcoded primary keys: admin_parameter.json is pk 1
# through 154, sample_model.json is pk 1, and so on. `loaddata` UPDATES the row
# at each id rather than skipping it, so running these against a populated
# database silently overwrites live records.
#
# That is a real hazard for this deployment: HSEO's models are being migrated in
# from NREL's instance, and if their reference data has drifted from the fixtures
# in this repo, an unconditional load on every container boot would quietly
# revert it. So we look before we write, and we fail closed if we cannot tell.
#
# To reseed on purpose, run the loaddata commands from the Getting Started docs
# by hand.
#
set -euo pipefail

SEEDED=$(python3 manage.py shell -c "
from api.models.calliope import Abstract_Tech, Parameter
from template.models import Template_Type
seeded = (
    Abstract_Tech.objects.exists()
    or Parameter.objects.exists()
    or Template_Type.objects.exists()
)
print('SEEDCHECK:' + ('yes' if seeded else 'no'))
" 2>/dev/null | grep -o 'SEEDCHECK:[a-z]*' | tail -n 1 | cut -d: -f2)

if [ "$SEEDED" = "yes" ]; then
  echo "Reference data already present -- skipping fixture load to protect existing rows."
  exit 0
fi

if [ "$SEEDED" != "no" ]; then
  echo "Could not determine whether reference data exists. Refusing to load fixtures." >&2
  echo "Fix the database connection, or load fixtures by hand once you have checked." >&2
  exit 1
fi

echo "Empty database detected -- loading reference data."

# api fixtures first: the template fixtures below reference api.Parameter and
# api.Abstract_Tech rows by id, and template/models.py runs a pre_save hook that
# looks them up. Load them the other way round and the whole batch rolls back.
python3 manage.py loaddata --app api \
      admin_abstract_tech.json \
      admin_parameter.json \
      admin_abstract_tech_param.json \
      admin_run_parameter.json

python3 manage.py loaddata --app template \
      admin_template_type.json \
      admin_template_type_variables.json \
      admin_template_type_techs.json \
      admin_template_type_locs.json \
      admin_template_type_loc_techs.json \
      admin_template_type_loc_tech_params.json \
      admin_template_type_tech_params.json \
      admin_template_type_carriers.json

echo "Reference data loaded."
