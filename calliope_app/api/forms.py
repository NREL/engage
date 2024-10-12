
from django import forms

from client.widgets import JSONEditorWidget

from api.models.engage import ComputeEnvironment


class ComputeEnvironmentModelForm(forms.ModelForm):
    class Meta:
        model = ComputeEnvironment
        fields = '__all__'
        widgets = {
            'solvers': JSONEditorWidget()
        }
