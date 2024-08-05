import json
import pandas as pd

# Load the JSON data from a file
with open('params.json', 'r') as file:
    data = json.load(file)

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
        'model': param['model']
    }
    rows.append(row)

# Create a DataFrame from the list of rows
df = pd.DataFrame(rows)

# Save the DataFrame to an Excel file
df.to_excel('parameters.xlsx', index=False)
