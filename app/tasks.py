from celery import shared_task

from .models import Document, OpenaiSettings
from .utils.processors.openai import chatgpt
from .utils.processors.pdf import extract_text_from_pdf

@shared_task
def process_pdf(document_id):
    document = Document.objects.get(id=document_id)

    try:
        settings = OpenaiSettings.objects.first()
        document.status = Document.Status.PROCESSING
        document.save()

        pdf_path = document.file.path
        extracted_text = extract_text_from_pdf(pdf_path)

        if not extracted_text:
            document.status = Document.Status.FAILED
            document.save()
            raise ValueError("No text extracted from PDF")

        messages = [
            {
                "role": "user",
                "content": f"{settings.summary_prompt}: {extracted_text}"
            }
        ]
        response = chatgpt(messages)

        document.summary = response.get("message", "Summary not found")
        document.status = Document.Status.DONE
        document.save()

    except Exception as e:
        document.status = Document.Status.FAILED
        document.save()
        raise e
