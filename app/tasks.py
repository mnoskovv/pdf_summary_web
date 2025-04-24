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
    """
        This module defines Celery tasks for processing PDF documents.

        Dependencies:
            - Relies on the Document model for managing document data.
            - Uses the OpenaiSettings model for configuration (e.g., summary prompt).
            - Utilizes the extract_text_from_pdf function to extract text from PDF files.
            - Interacts with OpenAI's ChatGPT API via the chatgpt function.

        Usage:
            - Call the `process_pdf` task with a document ID to process the document asynchronously.
    """
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
