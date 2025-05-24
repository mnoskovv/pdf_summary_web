from celery import shared_task
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangDocument

from .models import Document, DocumentChunk
from .utils.processors.pdf import extract_text_from_pdf
from .utils.processors.langchain import get_summary_chain, create_embeddings_and_store

def update_document_status(document, status):
    """
    Utility function to update a document's status in the database.

    Args:
        document (Document): The Document model instance.
        status (str): The new status to set (e.g., PROCESSING, DONE, FAILED).
    """
    document.status = status
    document.save()

@shared_task
def process_pdf(document_id):
    """
    Celery task for processing and summarizing the contents of a PDF document.

    This task performs the following steps:
    1. Loads the document by ID.
    2. Sets its status to "PROCESSING".
    3. Extracts text from the associated PDF file.
    4. Splits the text into smaller chunks for summarization.
    5. Creates LangChain document objects for each chunk.
    6. Loads a custom LangChain summarization chain (using map-reduce).
    7. Generates a final summary from all chunks.
    8. Saves the summary back to the document and updates the status to "DONE".
    9. In case of an error, sets the status to "FAILED".

    Args:
        document_id (int): The ID of the document to process.

    Raises:
        Exception: Any exception during processing will be re-raised after marking the document as FAILED.
    """

    # Retrieve the document object by ID
    document = Document.objects.get(id=document_id)
    try:
        update_document_status(document, Document.Status.PROCESSING)

        text = extract_text_from_pdf(document.file.path)
        if not text:
            raise ValueError("No text extracted from the PDF")

        # Разбиваем текст на чанки ОДИН раз
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)

        # Удаляем старые чанки (если есть)
        DocumentChunk.objects.filter(document=document).delete()

        # Сохраняем чанки в БД
        chunk_objs = [DocumentChunk(document=document, text=chunk) for chunk in chunks]
        DocumentChunk.objects.bulk_create(chunk_objs)

        # Загружаем чанки из БД (чтобы получить id и т.п.)
        chunk_objs = list(DocumentChunk.objects.filter(document=document))

        # Создаем LangChain документы
        docs = [LangDocument(page_content=chunk.text) for chunk in chunk_objs]

        # Суммаризация
        chain = get_summary_chain()
        summary = chain.run(docs)

        # Сохраняем summary
        document.summary = summary
        document.save()

        # Эмбеддинги для RAG (параллельно)
        create_embeddings_and_store(document, chunk_objs)

        update_document_status(document, Document.Status.DONE)

    except Exception as e:
        update_document_status(document, Document.Status.FAILED)
        raise e
