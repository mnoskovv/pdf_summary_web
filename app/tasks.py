from celery import shared_task

from .models import Document, OpenaiSettings
from .utils.processors.openai import chatgpt
from .utils.processors.pdf import extract_text_from_pdf

def update_document_status(document, status):
    """Utility function to update the document status and save it."""
    document.status = status
    document.save()

@shared_task
def process_pdf(document_id):
    document = Document.objects.get(id=document_id)

    try:
        settings = OpenaiSettings.objects.first()
        update_document_status(document, Document.Status.PROCESSING)

        pdf_path = document.file.path
        extracted_text = extract_text_from_pdf(pdf_path)

        if not extracted_text:
            update_document_status(document, Document.Status.FAILED)
            raise ValueError("No text extracted from PDF")

        messages = [
            {
                "role": "user",
                "content": f"{settings.summary_prompt}: {extracted_text}"
            }
        ]
        response = chatgpt(messages)

        if not response or response.get("status") != "Success":
            update_document_status(document, Document.Status.FAILED)
            return

        document.summary = response.get("message", "Summary not found")
        update_document_status(document, Document.Status.DONE)

    except Exception as e:
        update_document_status(document, Document.Status.FAILED)
        raise e
