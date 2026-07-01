import pdfplumber

def extract_pages_text(file_path: str) -> list[str]:
    """
    Abre o PDF usando pdfplumber e extrai o texto de cada página.
    Retorna uma lista de strings, onde cada string é o texto completo de uma página.
    """
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                pages_text.append("")
    return pages_text
