import json
import pandas as pd

# Load the JSON data from a file
with open('calliope_app/api/fixtures/admin_parameter.json', 'r', encoding='utf-8') as file:
    params = json.load(file)

with open('calliope_app/api/fixtures/admin_abstract_tech.json', 'r', encoding='utf-8') as file:
    abstract_techs_data = json.load(file)

with open('calliope_app/template/fixtures/admin_template_type_techs.json','r', encoding='utf-8') as file:
    techs_data = json.load(file)

with open('calliope_app/template/fixtures/admin_template_type.json','r', encoding='utf-8') as file:
    templates_data = json.load(file)

with open('calliope_app/template/fixtures/admin_template_type_tech_params.json','r', encoding='utf-8') as file:
    tech_params_data = json.load(file)

with open('calliope_app/template/fixtures/admin_template_type_loc_techs.json','r', encoding='utf-8') as file:
    loc_techs_data = json.load(file)

with open('calliope_app/template/fixtures/admin_template_type_loc_tech_params.json','r', encoding='utf-8') as file:
    loc_tech_params_data = json.load(file)

# Extract the list of parameter objects
parameter_objects = tech_params_data

# Create a list to hold the rows of the DataFrame
rows = []

# Loop through each parameter object and extract the fields
for param in parameter_objects:
    fields = param['fields']
    template_tech = [t for t in techs_data if t['pk'] == fields['template_tech']][0]
    abstract_tech = [t for t in abstract_techs_data if t['pk'] == template_tech['fields']['abstract_tech']][0]
    admin_param = [p for p in params if p['pk'] == fields['parameter']][0]
    template = [t for t in templates_data if t['pk'] == template_tech['fields']['template_type']][0]
    row = {
        'pk': param['pk'],
        'template': template['fields']['pretty_name'],
        'template_tech': template_tech['fields']['name'],
        'abstract_tech': abstract_tech['fields']['pretty_name'],
        'param_id': fields['parameter'],
        'param_name': admin_param['fields']['name'],
        'equation': fields['equation'],
        'index': json.dumps(fields['index']) if 'index' in fields else None,
        'dim': json.dumps(fields['dim']) if 'dim' in fields else None,
        'piecewise_dim': fields.get('piecewise_dim',''),
        'model':param['model']
    }
    rows.append(row)

# Create a DataFrame from the list of rows
df = pd.DataFrame(rows)
print(df[['pk','param_name','abstract_tech']])

# Save the DataFrame to an Excel file
df.to_excel('calliope_app/scripts/fixtures/template_tech_params.xlsx', index=False)

# Extract the list of parameter objects
parameter_objects = loc_tech_params_data

# Create a list to hold the rows of the DataFrame
rows = []

# Loop through each parameter object and extract the fields
for param in parameter_objects:
    fields = param['fields']
    template_loc_tech = [t for t in loc_techs_data if t['pk'] == fields['template_loc_tech']][0]
    template_tech = [t for t in techs_data if t['pk'] == template_loc_tech['fields']['template_tech']][0]
    abstract_tech = [t for t in abstract_techs_data if t['pk'] == template_tech['fields']['abstract_tech']][0]
    admin_param = [p for p in params if p['pk'] == fields['parameter']][0]
    template = [t for t in templates_data if t['pk'] == template_loc_tech['fields']['template_type']][0]
    row = {
        'pk': param['pk'],
        'template': template['fields']['pretty_name'],
        'template_loc_tech': fields['template_loc_tech'],
        'template_tech': template_tech['pk'],
        'template_tech_name': template_tech['fields']['name'],
        'abstract_tech': abstract_tech['fields']['pretty_name'],
        'param_id': fields['parameter'],
        'param_name': admin_param['fields']['name'],
        'equation': fields['equation'],
        'index': json.dumps(fields['index']) if fields['index'] else None,
        'dim': json.dumps(fields['dim']) if fields['dim'] else None,
        'piecewise_dim': fields.get('piecewise_dim',''),
        'model':param['model']
    }
    rows.append(row)

# Create a DataFrame from the list of rows
df = pd.DataFrame(rows)
print(df[['pk','param_name','abstract_tech']])

# Save the DataFrame to an Excel file
df.to_excel('calliope_app/scripts/fixtures/template_loc_tech_params.xlsx', index=False)
