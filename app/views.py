from django.shortcuts import render, redirect

from app.models import Document
from app.forms import DocumentUploadForm
from app.tasks import process_pdf


def upload_document_view(request):
    documents = Document.objects.order_by('-id')[:5]
    is_processing = Document.objects.filter(status='processing').exists()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid() and not is_processing:
            document = form.save()

            # run background task to process the PDF
            process_pdf.delay(document.id)
            return redirect('upload')
    else:
        form = DocumentUploadForm()

    return render(request, 'upload.html', {
        'form': form,
        'documents': documents,
        'is_processing': is_processing,
    })
