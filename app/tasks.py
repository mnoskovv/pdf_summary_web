from celery import shared_task
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangDocument

from .models import Document, DocumentChunk
from .utils.processors.pdf import extract_text_from_pdf
from .utils.processors.langchain import get_summary_chain, create_embeddings_and_store, get_title_generation_chain
from .utils.processors.youtube import extract_youtube_video_data
from pytube import YouTube


from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI

def update_document_status(document, status):
    """
    Utility function to update a document's status in the database.

    Args:
        document (Document): The Document model instance.
        status (str): The new status to set (e.g., PROCESSING, DONE, FAILED).
    """
    document.status = status
    document.save()


def get_youtube_video_title(url: str) -> str:
    """
    Получает название видео по ссылке на YouTube.
    Возвращает строку с названием или сообщение об ошибке.
    """
    try:
        yt = YouTube(url)
        return yt.title
    except Exception as e:
        return f"Ошибка при получении названия: {e}"


def extract_text_by_type(document):
    if document.variant == Document.Variant.DOCUMENT:
        return extract_text_from_pdf(document.file.path)
    elif document.variant == Document.Variant.YOUTUBE:
        text = extract_youtube_video_data(document.url)
        title = get_youtube_video_title(document.url)
        document.title = title if title else "Видео YouTube"
        document.save()
        return text
    else:
        return ""


@shared_task
def process_document(document_id):
    document = Document.objects.get(id=document_id)
    try:
        update_document_status(document, Document.Status.PROCESSING)

        # Получаем текст в зависимости от типа документа
        text = extract_text_by_type(document)

        if not text:
            raise ValueError("No text extracted from the document")

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

        if document.variant == Document.Variant.YOUTUBE:
            chain = get_title_generation_chain()
            generated_title = chain.run(summary_text=document.summary)
            document.title = generated_title
            print(f"Generated title: {generated_title}")

            document.save()
        update_document_status(document, Document.Status.DONE)

    except Exception as e:
        update_document_status(document, Document.Status.FAILED)
        raise e
