from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'title', 'url']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'accept': 'application/pdf',
                'class': 'form-control',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paste YouTube link here',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional title',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')

        if file and url:
            raise forms.ValidationError("You should provide either a file or a URL, not both.")

        if file:
            variant = Document.Variant.DOCUMENT

            if not file.name.lower().endswith('.pdf'):
                self.add_error('file', "Only PDF files allowed.")
            if file.size > 10 * 1024 * 1024:
                self.add_error('file', "File too large. Max 10 MB.")

            cleaned_data['variant'] = variant

        elif url:
            variant = Document.Variant.YOUTUBE

            if "youtube.com" not in url and "youtu.be" not in url:
                self.add_error('url', "Enter a valid YouTube URL.")

            cleaned_data['variant'] = variant

        else:
            raise forms.ValidationError("Either a file or a URL must be provided.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.variant = self.cleaned_data.get('variant')
        if commit:
            instance.save()
        return instance
