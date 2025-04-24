import fitz

def extract_text_from_pdf(file_path: str) -> str:
    """
    This processor provides functionality to extract text from PDF files.
    """

    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()
