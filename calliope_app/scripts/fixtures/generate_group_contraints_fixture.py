import json
import pandas as pd

def generate_constraints_json(df):
    json_list = []
    pk = 1

    for index, row in df.iterrows():
        name = row['Name']
        value = row['Dimensions']
        description = row['Description']

        # Convert the name to pretty_name
        pretty_name = name.replace('_', ' ').title()

        json_obj = {
            "pk": pk,
            "model": "api.group_constraint",
            "fields": {
                "name": name,
                "pretty_name": pretty_name,
                "description": description,
                "where": "",
                "equations": [
                    {
                        "expression": ""
                    }
                ],
                "slices": {
                    "techs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "techs"
                    },
                    "techs_lhs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "techs"
                    },
                    "techs_rhs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "techs"
                    },
                    "locs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "locs"
                    },
                    "locs_lhs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "locs"
                    },
                    "locs_rhs": {
                        "yaml": [
                            {
                                "expression": "[VALUE]"
                            }
                        ],
                        "dim": "locs"
                    }
                },
                "sub_expression": {
                    "value_1": {
                        "yaml": [
                            {
                                "expression": "VALUE"
                            }
                        ],
                        "show": True
                    }
                }
            }
        }

        if value == "carriers":
            json_obj["fields"]["slices"]["carriers_lhs"] = {
                "yaml": [
                    {
                        "expression": "[VALUE]"
                    }
                ],
                "dim": "carriers"
            }
            json_obj["fields"]["slices"]["carriers_rhs"] = {
                "yaml": [
                    {
                        "expression": "[VALUE]"
                    }
                ],
                "dim": "carriers"
            }

        if value == "costs":
            json_obj["fields"]["slices"]["costs"] = {
                "yaml": [
                    {
                        "expression": "[VALUE]"
                    }
                ],
                "dim": "costs"
            }

        json_list.append(json_obj)
        pk += 1

    return json_list

input_file = "group_constraints_fixture.xlsx"
df = pd.read_excel(input_file)

json_output = generate_constraints_json(df)

output_file = "constraints_output.json"
with open(output_file, "w") as f:
    json.dump(json_output, f, indent=2)

print(f"JSON data written to {output_file}")
