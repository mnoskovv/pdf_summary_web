from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.pdf'):
            raise forms.ValidationError("Only PDF-files allowed.")
        # 10 MB limit
        if file.size > 10 * 1024 * 1024:  
            raise forms.ValidationError("File too large Max 10 mb.")
        return file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'application/pdf'
        })