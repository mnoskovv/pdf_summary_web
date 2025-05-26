import os
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain, LLMChain


from app.models import OpenaiSettings, Message


def get_title_generation_chain():
    """
    Создаёт LangChain цепочку для генерации короткого заголовка видео из текста саммари.

    Функция:
    - Получает настройки OpenAI из базы (модель, температуру).
    - Инициализирует ChatOpenAI с этими настройками.
    - Формирует промпт, который принимает summary и просит сгенерировать короткий заголовок.
    - Возвращает готовую цепочку LLMChain, готовую к вызову.

    Возвращает:
        LLMChain для генерации заголовка.
    Исключения:
        ValueError — если настройки OpenAI не найдены.
    """

    settings = OpenaiSettings.objects.first()
    if not settings:
        raise ValueError("OpenAI settings not found")

    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=settings.model,
        temperature=float(settings.temperature),
    )

    prompt = PromptTemplate(
        input_variables=["summary_text"],
        template=(
            "На основе следующего краткого описания видео (саммари), "
            "сгенерируй короткое, ёмкое и привлекательное название видео на русском языке.\n\n"
            "Саммари:\n{summary_text}\n\n"
            "Название (не длиннее 60 символов):"
        )
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    return chain


def get_summary_chain():
    """
    Creates a LangChain summarization chain using custom prompts from the database.

    This function:
    - Loads the OpenAI model and prompt settings from the `OpenaiSettings` model.
    - Initializes a ChatOpenAI instance with the specified model and temperature.
    - Defines two custom prompts: one for summarizing individual chunks (map step),
      and another for combining the partial summaries into a final one (reduce step).
    - Returns a ready-to-use LangChain summarization chain using the "map_reduce" method.

    Returns:
        A LangChain summarize chain object configured for multi-step summarization.
    Raises:
        ValueError: If OpenAI settings are not found in the database.
    """

    # Get OpenAI API configuration from the database
    settings = OpenaiSettings.objects.first()
    if not settings:
        raise ValueError("OpenAI settings not found")

    # Initialize the ChatOpenAI model with your API key and settings
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=settings.model,
        temperature=float(settings.temperature),
    )

    # Промт для суммирования отдельных частей документа
    map_prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Прочитай следующий фрагмент документа и напиши краткое резюме его основной идеи.\n\n"
            "Фрагмент:\n{text}\n\n"
            "Резюме:"
        )
    )

    # Промт для объединения всех частичных резюме в итоговое
    combine_prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Тебе дана серия резюме различных частей длинного документа.\n"
            "Используя эти резюме, напиши связное и краткое итоговое резюме всего документа.\n\n"
            "Резюме частей:\n{text}\n\n"
            "Итоговое резюме:"
        )
    )

    # Create a summarize chain using the map-reduce strategy
    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
    )

    return chain


BASE_DIR = Path(__file__).resolve().parent.parent.parent
FAISS_DIR = BASE_DIR / "faiss_indices"
FAISS_DIR.mkdir(parents=True, exist_ok=True)

def create_embeddings_and_store(document, chunk_objs):
    texts = [chunk.text for chunk in chunk_objs]
    embeddings_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vectorstore = FAISS.from_texts(texts, embeddings_model)

    faiss_index_path = FAISS_DIR / f"faiss_index_doc_{document.id}"
    vectorstore.save_local(str(faiss_index_path))


def answer_question_with_rag_and_history(document_id, question):
    # Get the OpenAI API key and LangChain settings from the environment/database
    api_key = os.getenv("OPENAI_API_KEY")
    settings = OpenaiSettings.objects.first()

    if not settings:
        raise ValueError("OpenAI settings not found")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment.")

    # --- Step 1: Load the FAISS vector store for this document ---
    embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)
    faiss_index_path = FAISS_DIR / f"faiss_index_doc_{document_id}"
    if not faiss_index_path.exists():
        raise FileNotFoundError(f"FAISS index not found at {faiss_index_path}")

    # Load previously stored vector index from disk
    vectorstore = FAISS.load_local(
        str(faiss_index_path),
        embeddings_model,
        allow_dangerous_deserialization=True  # only use this if you trust the data
    )

    # --- Step 2: Perform similarity search with the current question ---
    # Find top-k most relevant text chunks using semantic similarity
    similar_docs = vectorstore.similarity_search(question, k=4)

    # --- Step 3: Retrieve conversation history related to this document ---
    # Fetch all past user and assistant messages, sorted chronologically
    past_messages = Message.objects.filter(document_id=document_id).order_by("created_at")
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in past_messages
    ]

    # Temporarily add the current question to the end of the chat history
    chat_history.append({"role": "user", "content": question})

    # --- Step 4: Initialize the language model and create a conversational RAG chain ---
    llm = ChatOpenAI(
        temperature=0,
        model=settings.model,
        openai_api_key=api_key
    )

    # Use ConversationalRetrievalChain to handle context-aware Q&A
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=False  # Set to True if you want to return docs for debugging or traceability
    )

    # Run the chain: it reformulates the question using history and retrieves relevant docs
    result = chain({
        "question": question,
        "chat_history": [(m["role"], m["content"]) for m in chat_history[:-1]]  # history without the last question
    })

    answer = result["answer"]

    # --- Step 5: Persist the question and generated answer to the database ---
    Message.objects.create(document_id=document_id, role="user", content=question)
    Message.objects.create(document_id=document_id, role="assistant", content=answer)

    return answer
