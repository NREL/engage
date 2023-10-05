from google.cloud import translate_v2

# key_path = r"/Users/mpillodi/Documents/GitHub/engage/nrel-gcp-engage-service-account.json"

# translate_client = translate_v2.Client.from_service_account_json(key_path)

# text_to_translate1 = 'Annual qty. per unit carying capacity'
# text_to_translate2 = "Calliope: costs.CO2e.om_annual<br><br>Fixed annual equivalent emissions quantity per unit carrying capacity. Can be used, e.g., for fixed annual emissions associated with production capacity of the technology."

# translated_text1 = translate_client.translate(text_to_translate1, source_language = 'en', target_language = 'es')
# translated_text2 = translate_client.translate(text_to_translate2, source_language = 'en', target_language = 'es')

# translate_text1 = translated_text1['translatedText']
# translate_text2 = translated_text2['translatedText']

# print(f"Original: (English) {text_to_translate1}")
# print(f"Translated Text: (Spanish){translate_text1}")
# print("************************************************")
# print(f"Original: (English) {text_to_translate2}")
# print(f"Translated Text: (Spanish){translate_text2}")

import os
from google.cloud import translate_v2
import polib

def translate_text(text, source_language, target_language):
    key_path = r"/Users/mpillodi/Documents/GitHub/engage/nrel-gcp-engage-service-account.json"
    translate_client = translate_v2.Client.from_service_account_json(key_path)
    translated_text = translate_client.translate(text, source_language=source_language, target_language=target_language)
    return translated_text['translatedText']

def translate_po_file(input_file, output_file, source_language, target_language):
    # Load the input PO file
    po = polib.pofile(input_file)

    # Iterate through entries and translate
    for entry in po:
        if entry.msgid:
            translated_text = translate_text(entry.msgid, source_language, target_language)
            entry.msgstr = translated_text

    # Save the translated PO file
    po.save(output_file)

if __name__ == "__main__":
    input_file = "/Users/mpillodi/Documents/GitHub/engage/calliope_app/locale/es/LC_MESSAGES/django.po"  # Replace with the path to your input PO file 
    output_file = "/Users/mpillodi/Documents/GitHub/engage/calliope_app/locale/es/LC_MESSAGES/output.po"  # Replace with the path to your output PO file
    source_language = "en"  # Source language (English in this case)
    target_language = "es"  # Target language (Spanish in this case)

    translate_po_file(input_file, output_file, source_language, target_language)

    print(f"Translation complete. Saved to {output_file}")
