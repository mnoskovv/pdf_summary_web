from celery import shared_task
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangDocument

from .models import Document
from .utils.processors.pdf import extract_text_from_pdf
from .utils.processors.langchain import get_summary_chain  # <- используем новую функцию

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
        # Mark the document as "processing"
        update_document_status(document, Document.Status.PROCESSING)

        # Extract text from the uploaded PDF file
        text = extract_text_from_pdf(document.file.path)
        if not text:
            raise ValueError("No text extracted from the PDF")

        # Split text into smaller overlapping chunks for better summarization
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(text)

        # Wrap each chunk as a LangChain document
        docs = [LangDocument(page_content=chunk) for chunk in chunks]

        # Load the custom summarization chain with map/reduce prompts
        chain = get_summary_chain()

        # Run the chain on the document chunks to produce a summary
        summary = chain.run(docs)

        # Save the summary and mark the document as "done"
        document.summary = summary
        update_document_status(document, Document.Status.DONE)

    except Exception as e:
        # If something goes wrong, mark the document as "failed"
        update_document_status(document, Document.Status.FAILED)
        raise e
