from django import forms
from .models import FileAsset


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = FileAsset
        fields = ["title", "file", "category", "description"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "rounded-md border px-3 py-2 text-sm",
                "placeholder": "File title",
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "rounded-md border px-3 py-2 text-sm",
            }),
            "category": forms.Select(attrs={
                "class": "rounded-md border px-3 py-2 text-sm",
            }),
            "description": forms.Textarea(attrs={
                "class": "rounded-md border px-3 py-2 text-sm",
                "rows": 3,
                "placeholder": "Optional description",
            }),
        }