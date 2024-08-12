import json
import pandas as pd

# Load the JSON data from a file
with open('calliope_app/api/fixtures/admin_parameter.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

with open('calliope_app/api/fixtures/admin_abstract_tech_param.json','r', encoding='utf-8') as file:
    tech_params_data = json.load(file)

with open('calliope_app/api/fixtures/admin_abstract_tech.json', 'r', encoding='utf-8') as file:
    abstract_techs_data = json.load(file)
# Extract the list of parameter objects
parameter_objects = data

# Create a list to hold the rows of the DataFrame
rows = []

# Loop through each parameter object and extract the fields
for param in parameter_objects:
    fields = param['fields']
    row = {
        'pk': param['pk'],
        'category': fields['category'],
        'category_fr': fields['category_fr'],
        'category_es': fields['category_es'],
        'pretty_name': fields['pretty_name'],
        'pretty_name_fr': fields['pretty_name_fr'],
        'pretty_name_es': fields['pretty_name_es'],
        'description': fields['description'],
        'description_fr': fields['description_fr'],
        'description_es': fields['description_es'],
        'root': fields['root'],
        'name': fields['name'],
        'timeseries_enabled': fields['timeseries_enabled'],
        'is_systemwide': fields['is_systemwide'],
        'units': fields['units'],
        'is_systemwide': fields['is_systemwide'],
        'is_essential': fields['is_essential'],
        'is_carrier': fields['is_carrier'],
        'choices': fields['choices'],
        'tags': fields['tags'],
        'model': param['model'],
        #'index': fields['index'],
        #'dim': fields['dim'],
        'abstract_techs': json.dumps([t['fields']['name'] for t in abstract_techs_data if str(t['pk']) in [tp['fields']['abstract_tech_id'] for tp in tech_params_data if tp['fields']['parameter_id'] == str(param['pk'])]])
    }
    rows.append(row)

# Create a DataFrame from the list of rows
df = pd.DataFrame(rows)
print(df[['pk','name','abstract_techs']])

# Save the DataFrame to an Excel file
df.to_excel('calliope_app/scripts/fixtures/parameters.xlsx', index=False)
