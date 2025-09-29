import pandas as pd
import json

# Load the Excel file into a DataFrame
df_l = pd.read_excel('calliope_app/scripts/fixtures/template_loc_tech_params.xlsx')

# Initialize the list to hold the parameter objects
parameter_objects = []

# Initialize the list to hold the tech parameter objects
admin_tech_param_objects = []
admin_tech_param_index = 1

# Iterate through each row in the DataFrame
for index, row in df_l.iterrows():
    param = {
        "pk": row['pk'],
        "fields": {
            "template_loc_tech": row['template_loc_tech'],
            "parameter": row['param_id'],
            "equation": row['equation'],
            "index": json.loads(row['index']) if pd.notna(row['index']) else None,
            "dim": json.loads(row['dim']) if pd.notna(row['dim']) else None,
            "piecewise_dim": row['piecewise_dim'] if pd.notna(row['piecewise_dim']) else None
        },
        "model": row['model']
    }
    parameter_objects.append(param)

# Convert the list of parameter objects to JSON
json_data = json.dumps(parameter_objects, indent=2, ensure_ascii=False)

# Save the JSON data to a file
with open('calliope_app/template/fixtures/admin_template_type_loc_tech_params.json', 'w', encoding='utf-8') as file:
    file.write(json_data)

print("Conversion complete. The data has been saved to 'admin_template_type_loc_tech_params.json' and 'admin_template_type_tech_params.json'.")
