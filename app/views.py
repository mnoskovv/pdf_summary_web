from django.shortcuts import render, redirect
from django.http import JsonResponse

from app.models import Document
from app.forms import DocumentUploadForm
from app.tasks import process_pdf


# api endpoint to get the latest 5 documents using polling approach
def get_documents(request):
    documents = Document.objects.order_by('-id')[:5]
    docs_data = []

    for doc in documents:
        docs_data.append({
            'id': doc.id,
            'filename': doc.filename(),
            'status': doc.status,
            'status_display': doc.get_status_display(),
            'summary': doc.summary,
        })
    
    return JsonResponse({'documents': docs_data})

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
