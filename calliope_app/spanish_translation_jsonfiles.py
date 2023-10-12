import json
from google.cloud import translate_v2

def translate_text(text, source_language, target_language):
    # Replace with your own service account key file path
    key_path = r"/Users/mpillodi/Documents/GitHub/engage/nrel-gcp-engage-service-account.json"
    translate_client = translate_v2.Client.from_service_account_json(key_path)
    translated_text = translate_client.translate(text, source_language=source_language, target_language=target_language)
    return translated_text['translatedText']

# Load the JSON data
with open('/Users/mpillodi/Documents/GitHub/engage/calliope_app/api/fixtures/admin_run_parameter.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Translate and update the JSON data
for item in data:
    fields = item['fields']
    source_language = 'en'  

    # Translate pretty_name and description
    pretty_name = fields.get('pretty_name', '')
    description = fields.get('description', '')

    if pretty_name:
        fields['pretty_name_es'] = translate_text(pretty_name, source_language, 'es')

    if description:
        fields['description_es'] = translate_text(description, source_language, 'es')

# Save the updated JSON data
with open('translated_json_file.json', 'w', encoding='utf-8') as translated_json_file:
    json.dump(data, translated_json_file, ensure_ascii=False, indent=2)
