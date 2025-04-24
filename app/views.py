from django.shortcuts import render, redirect

from app.models import Document
from app.utils.processors.pdf import extract_text_from_pdf
from .forms import DocumentUploadForm


def upload_document_view(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('upload_success')
    else:
        form = DocumentUploadForm()
    return render(request, 'upload.html', {'form': form})


def upload_success_view(request):
    document = Document.objects.latest('id')
    pdf_path = document.file.path
    extracted_text = extract_text_from_pdf(pdf_path)

    return render(request, 'success.html', {
        'document': document,
        'extracted_text': extracted_text,
    })