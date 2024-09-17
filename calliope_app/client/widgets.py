import json

from django import forms
from django.utils.safestring import mark_safe

class JSONEditorWidget(forms.Textarea):
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/jsoneditor@9.9.0/dist/jsoneditor.min.css',)
        }
        js = ('https://cdn.jsdelivr.net/npm/jsoneditor@9.9.0/dist/jsoneditor.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        editor_id = attrs.get('id', name)
        editor_script = f"""
        <style>
            .jsoneditor .jsoneditor-menu {{
                background: #79aec8 !important;
            }}
        </style>
        <div id="jsoneditor-{editor_id}" style="width: 100%; height: 400px;"></div>
        <script>
            (function() {{
                var container = document.getElementById("jsoneditor-{editor_id}");
                var options = {{
                    mode: 'code',  // Can be 'tree', 'form', 'text', 'code', or 'view'
                    onChange: function() {{
                        var json = editor.get();
                        document.getElementById("{editor_id}").value = JSON.stringify(json, null, 2);
                    }}
                }};
                var editor = new JSONEditor(container, options);
                var initialValue = {value};
                if (initialValue) {{
                    editor.set(initialValue);
                }}
            }})();
        </script>
        <textarea id="{editor_id}" name="{name}" style="display:none;">{value}</textarea>
        """
        return mark_safe(editor_script)
