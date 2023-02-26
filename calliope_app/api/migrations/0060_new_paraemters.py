from django.db import migrations, models
import logging

def get_console_logger():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("starting logger")
    return logger

''' 
    This migration uses the new Parameter and Abstract_Tech_Param records to build a dict
    describing the technology <-> parameter mapping for each root+name combination, then
    looping through all Tech_Param and Loc_Tech_Param records and updating the parameters
    on any records that don't match the new mapping.
    
    The migration assumes/relies on the fact that any newly named parameters for specific
    technologies that need to be migrated share the same root+name as the old "general purpose"
    parameters we need to migrate the Tech_Param and Loc_Tech_Param records from.
'''
def adjust_params(apps, schema_editor):
    logger = get_console_logger()
    Abs_Tech_Dict = {}
    Abs_Tech_Params = apps.get_model('api', 'Abstract_Tech_Param').objects.all()
    Params = apps.get_model('api', 'Parameter').objects.all()
    for row in Params:
        Abs_Tech_Dict[row.root+row.name] = {}
    for row in Abs_Tech_Params:
        Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.abstract_tech.id] = (row.parameter.id,row.parameter)
    Tech_Params = apps.get_model('api', 'Tech_Param').objects.all()
    for row in Tech_Params:
        if row.parameter.id != Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.technology.abstract_tech.id][0]:
            logger.info(str(row.parameter.id)+' to '+str(Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.technology.abstract_tech.id][0]))
            row.parameter = Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.technology.abstract_tech.id][1]
            row.save(update_fields=['parameter'])
    Loc_Tech_Params = apps.get_model('api', 'Loc_Tech_Param').objects.all()
    for row in Loc_Tech_Params:
        if row.parameter.id != Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.loc_tech.technology.abstract_tech.id][0]:
            logger.info(str(row.parameter.id)+' to '+str(Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.loc_tech.technology.abstract_tech.id][0]))
            row.parameter = Abs_Tech_Dict[row.parameter.root+row.parameter.name][row.loc_tech.technology.abstract_tech.id][1]
            row.save(update_fields=['parameter'])

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0059_auto_20230104_0139'),
    ]

    operations = [
        migrations.RunPython(adjust_params)
    ]