import os
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain

from app.models import OpenaiSettings

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

    # Prompt used to summarize individual chunks of the document
    map_prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Read the following excerpt from a document and write a concise summary of its main idea.\n\n"
            "Excerpt:\n{text}\n\n"
            "Summary:"
        )
    )

    # Prompt used to combine all chunk summaries into a single final summary
    combine_prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "You are given a list of summaries of different sections from a long document.\n"
            "Using these summaries, write a coherent and concise overall summary of the full document.\n\n"
            "Section summaries:\n{text}\n\n"
            "Final summary:"
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


def answer_question_with_rag(document_id, question):
    api_key = os.getenv("OPENAI_API_KEY")

    settings = OpenaiSettings.objects.first()
    if not settings:
        raise ValueError("OpenAI settings not found")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment.")

    embeddings_model = OpenAIEmbeddings(openai_api_key=api_key)

    faiss_index_path = FAISS_DIR / f"faiss_index_doc_{document_id}"
    if not faiss_index_path.exists():
        raise FileNotFoundError(f"FAISS index not found at {faiss_index_path}")

    vectorstore = FAISS.load_local(
        str(faiss_index_path),
        embeddings_model,
        allow_dangerous_deserialization=True
    )

    similar_docs = vectorstore.similarity_search(question, k=4)

    llm = ChatOpenAI(
        temperature=0,
        model=settings.model,
        openai_api_key=api_key
    )
    chain = load_qa_chain(llm, chain_type="stuff")

    answer = chain.run(input_documents=similar_docs, question=question)
    return answer
