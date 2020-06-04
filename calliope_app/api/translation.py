from modeltranslation.translator import translator, TranslationOptions

from api.models.calliope import Parameter, Abstract_Tech, Run_Parameter
from api.models.engage import Help_Guide


class HelpGuideTranslationOptions(TranslationOptions):
    
    fields = ("html", )


class ParameterTranslationOptions(TranslationOptions):
    
    fields = ("category", "pretty_name", "description")


class AbstractTechTranslationOptions(TranslationOptions):
    
    fields = ("pretty_name", "description")


class RunParameterTranslationOptions(TranslationOptions):
    
    fields = ("pretty_name", "description")


translator.register(Help_Guide, HelpGuideTranslationOptions)
translator.register(Parameter, ParameterTranslationOptions)
translator.register(Abstract_Tech, AbstractTechTranslationOptions)
translator.register(Run_Parameter, RunParameterTranslationOptions)
