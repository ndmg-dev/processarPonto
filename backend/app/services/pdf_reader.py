import fitz

def extract_pages_text(file_path: str) -> list[str]:
    """
    Abre o PDF usando PyMuPDF (fitz) e extrai o texto de cada página.
    Retorna uma lista de strings, onde cada string é o texto completo de uma página.
    """
    doc = fitz.open(file_path)
    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        pages_text.append(text)
    doc.close()
    return pages_text
