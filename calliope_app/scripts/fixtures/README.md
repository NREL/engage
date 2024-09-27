# NREL Engage Fixture Scripts: 
These scripts are used to update fixtures, mainly admin tables for Engage. The examples committed are for the Admin Parameters table but it could be altered for any fixture. It is recommended to keep the pk keys in place, especially for admin tables as to not alter existing data.

## convert_to_excel.py
- Provide a document in the same directory params.json file
- Will generate a params.xlsx file

## convert_to_fixture.py
- Provide a document in the same directory params.xlsx file
- Will generate a params.json file