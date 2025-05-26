import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from prometheus_client import Counter
from django.views.decorators.csrf import csrf_exempt

from app.models import Document, Message
from app.forms import DocumentUploadForm
from app.tasks import process_document
from app.utils.processors.langchain import answer_question_with_rag_and_history

# Простая метрика: сколько раз вызывали health check
health_check_counter = Counter('health_check_requests_total', 'Total health check requests')

# api endpoint to get the latest 5 documents using polling approach
def get_documents(request):
    documents = Document.objects.order_by('-id')[:5]
    docs_data = []

    for doc in documents:
        docs_data.append({
            'id': doc.id,
            'filename': doc.filename() if doc.variant == Document.Variant.DOCUMENT else None,
            'variant': doc.variant,
            'title': doc.title,
            'url': doc.url,
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
            process_document.delay(document.id)
        return redirect('upload')
    else:
        form = DocumentUploadForm()

    return render(request, 'upload.html', {
        'form': form,
        'documents': documents,
        'is_processing': is_processing,
    })


def document_chat_view(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    # Получаем все сообщения по документу, отсортированные по времени
    messages = Message.objects.filter(document_id=doc_id).order_by("created_at")

    return render(request, 'document_chat.html', {
        'document': document,
        'messages': messages,
    })


@csrf_exempt
def ask_question(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            question = body.get("question")
            document_id = body.get("document_id")
            if not question or not document_id:
                return JsonResponse({"error": "Missing question or document_id"}, status=400)

            # Используем функцию с поддержкой истории сообщений
            answer = answer_question_with_rag_and_history(document_id, question)

            return JsonResponse({"answer": answer})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def health_check_view(request):
    health_check_counter.inc()
    return JsonResponse({'status': 'ok'})
