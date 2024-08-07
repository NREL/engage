import pandas as pd
import json

# Load the Excel file into a DataFrame
df = pd.read_excel('C7_Admin_Parameters_Fixture_Update.xlsx')

# Initialize the list to hold the parameter objects
parameter_objects = []

# Iterate through each row in the DataFrame
for index, row in df.iterrows():
    param = {
        "pk": index + 1, # or row['pk']
        "fields": {
            "category": "" if pd.isna(row['category']) else row['category'],
            "category_fr": "" if pd.isna(row['category_fr']) else row['category_fr'],
            "category_es": "" if pd.isna(row['category_es']) else row['category_es'],
            "pretty_name": "" if pd.isna(row['pretty_name']) else row['pretty_name'],
            "pretty_name_fr": "" if pd.isna(row['pretty_name_fr']) else row['pretty_name_fr'],
            "pretty_name_es": "" if pd.isna(row['pretty_name_es']) else row['pretty_name_es'],
            "description": "" if pd.isna(row['description']) else row['description'],
            "description_fr": "" if pd.isna(row['description_fr']) else row['description_fr'],
            "description_es": "" if pd.isna(row['description_es']) else row['description_es'],
            "root": "" if pd.isna(row['root']) else row['root'],
            "name": "" if pd.isna(row['name']) else row['name'],
            "timeseries_enabled": "True" if row['timeseries_enabled'] == 1.0 else "False",
            "is_systemwide": "True" if row['is_systemwide'] == 1.0 else "False",
            "units": "" if pd.isna(row['units']) else row['units'],
            "is_essential": "True" if row['is_essential'] == 1.0 else "False",
            "is_carrier": "True" if row['is_carrier'] == 1.0 else "False",
            "choices": row['choices'] if pd.notna(row['choices']) else "[]",
            "tags": row['tags'] if pd.notna(row['tags']) else "[]",
            "index": json.dumps(row['index'].split(',')) if pd.notna(row['index']) else "[]",
            "dim": json.dumps(row['dims'].split(',')) if pd.notna(row['dims']) else "[]"
        },
        "model": row['model']
    }
    parameter_objects.append(param)

# Convert the list of parameter objects to JSON
json_data = json.dumps(parameter_objects, indent=2, ensure_ascii=False)

# Save the JSON data to a file
with open('parameters_converted.json', 'w') as file:
    file.write(json_data)

print("Conversion complete. The data has been saved to 'parameters_converted.json'.")
