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

def extract_pages_words(file_path: str) -> list[list[tuple]]:
    """
    Abre o PDF usando PyMuPDF (fitz) e extrai as palavras de cada página com suas
    coordenadas (x0, y0, x1, y1, texto, ...). O espelho de ponto é um layout
    tabular onde cada célula vira uma linha de texto separada e fora de ordem
    quando lido apenas como texto puro, então as coordenadas são necessárias
    para reconstruir corretamente as linhas/colunas de cada dia.
    """
    doc = fitz.open(file_path)
    pages_words = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        words = page.get_text("words")
        pages_words.append(words)
    doc.close()
    return pages_words
