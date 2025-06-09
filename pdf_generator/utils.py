import os
import tarfile
import logging
import requests
import shutil
import pdfkit
import unicodedata
import re
from bs4 import BeautifulSoup
from django.conf import settings
from io import BytesIO
from typing import Dict, Tuple, Optional
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

BASE_URL = "https://pdinfinita.com/googledrive/PTEC"

def fix_portuguese_chars(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text

    # Normalize to NFC to compose characters correctly
    text = unicodedata.normalize('NFC', text)

    # Comprehensive mapping for Portuguese special characters and common encoding issues
    portuguese_char_map = {
        # Lowercase accented vowels
        'Ã¡': 'á', 'Ã£': 'ã', 'Ã¢': 'â', 'Ãà': 'à', 'Ãä': 'ä',
        'Ãé': 'é', 'Ãê': 'ê', 'Ãè': 'è', 'Ã«': 'ë',
        'Ãí': 'í', 'Ãì': 'ì', 'Ãî': 'î', 'Ãï': 'ï',
        'Ã³': 'ó', 'Ãµ': 'õ', 'Ãô': 'ô', 'Ãò': 'ò', 'Ãö': 'ö',
        'Ãº': 'ú', 'Ã»': 'û', 'Ãù': 'ù', 'Ãü': 'ü',
        # Uppercase accented vowels
        'Ã': 'Á', 'Ã': 'Ã', 'Ã': 'Â', 'Ã': 'À', 'Ã': 'Ä',
        'Ã': 'É', 'Ã': 'Ê', 'Ã': 'È', 'Ã': 'Ë',
        'Ã': 'Í', 'Ã': 'Ì', 'Ã': 'Î', 'Ã': 'Ï',
        'Ã': 'Ó', 'Ã': 'Õ', 'Ã': 'Ô', 'Ã': 'Ò', 'Ã': 'Ö',
        'Ã': 'Ú', 'Ã': 'Û', 'Ã': 'Ù', 'Ã': 'Ü',
        # Cedilla
        'Ã§': 'ç', 'Ã': 'Ç',
        # Common broken sequences
        'Ã§Ã£': 'ção', 'Ã§Ãµ': 'ções', 'Ã£o': 'ão', 'Ãµes': 'ões',
        # Common misspellings and encoding artifacts
        'CapÃ­tulo': 'Capítulo', 'CapÃ': 'Capítulo',
        'econÃ´mica': 'econômica', 'patrimÃ´nio': 'patrimônio',
        # Punctuation and symbols
        'â': '‚', 'â': '„', 'â¦': '…', 'â¡': '‡', 'â°': '‰',
        'â¹': '‹', 'â': "'", 'â': "'", 'â': '"', 'â': '"',
        'â¢': '•', 'â': '–', 'â': '—', 'â¢': '™', 'âº': '›',
        'Â°': '°', 'Â±': '±', 'Â´': "'", 'Âµ': 'µ', 'Â·': '·',
        'Âº': 'º', 'Â»': '»', 'Â¼': '¼', 'Â½': '½', 'Â¾': '¾', 'Â¿': '¿',
        # Remove stray encoding artifacts
        'Ã ': ' ', 'â': '"', 'Â': ''
    }

    # Apply basic replacements
    for wrong, right in portuguese_char_map.items():
        text = text.replace(wrong, right)

    # Handle complex broken sequences with regex
    def fix_broken_sequence(match):
        sequence = match.group(0)
        base_char = sequence[0]
        replacements = {
            'a': {'Ì o': 'ão', 'Ì§': 'ã', 'Ì£': 'à', 'Ì': 'â', 'Ã': 'ã', 'Ì¤': 'ä'},
            'e': {'Ì§': 'ê', 'Ì ': 'é', 'Ì': 'ê', 'Ã': 'ê', 'Ì': 'ë'},
            'i': {'Ì ': 'í', 'Ã': 'í', 'Ì': 'î', 'Ì': 'ï'},
            'o': {'Ì es': 'ões', 'Ì§': 'õ', 'Ì ': 'ó', 'Ì': 'ô', 'Ã': 'ô', 'Ì': 'ö'},
            'u': {'Ì ': 'ú', 'Ã': 'ú', 'Ì': 'û', 'Ì': 'ü'},
            'c': {'Ì§': 'ç', 'Ã': 'ç'},
            'A': {'Ì o': 'ÃO', 'Ì§': 'Ã', 'Ì£': 'À', 'Ì': 'Â', 'Ã': 'Ã', 'Ì¤': 'Ä'},
            'E': {'Ì§': 'Ê', 'Ì ': 'É', 'Ì': 'Ê', 'Ã': 'Ê', 'Ì': 'Ë'},
            'I': {'Ì ': 'Í', 'Ã': 'Í', 'Ì': 'Î', 'Ì': 'Ï'},
            'O': {'Ì es': 'ÕES', 'Ì§': 'Õ', 'Ì ': 'Ó', 'Ì': 'Ô', 'Ã': 'Ô', 'Ì': 'Ö'},
            'U': {'Ì ': 'Ú', 'Ã': 'Ú', 'Ì': 'Û', 'Ì': 'Ü'},
            'C': {'Ì§': 'Ç', 'Ã': 'Ç'}
        }
        if base_char in replacements:
            for broken, correct in replacements[base_char].items():
                if broken in sequence:
                    return correct
        return base_char

    # Regex pattern for broken sequences
    pattern = r'[aeioucAEIOUC](?:Ì[\s§es£\^¤\^]|Ã)'
    text = re.sub(pattern, fix_broken_sequence, text)

    # Clean up remaining artifacts
    text = re.sub(r'[\x00-\x1F\x7F-\x9FÌ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Final encoding normalization
    text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    return text

def extract_tar_gz(tar_path, extract_dir):
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(extract_dir)
        logger.info(f"extract_tar_gz: Extraído {tar_path} para {extract_dir}")
    except Exception as e:
        logger.error(f"extract_tar_gz: Erro ao extrair {tar_path}: {str(e)}")
        raise

def fetch_html_content(url):
    try:
        response = requests.get(url, timeout=40, verify=False)
        response.raise_for_status()
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        if soup.find(['html', 'body']) and len(content.strip()) > 100:
            logger.info(f"fetch_html_content: Conteúdo HTML válido baixado de {url}")
            return content
        else:
            logger.warning(f"fetch_html_content: Conteúdo inválido ou vazio em {url}")
            return None
    except requests.RequestException as e:
        logger.warning(f"fetch_html_content: Erro ao baixar {url}: {str(e)}")
        return None

def clean_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for iframe in soup.find_all('iframe'):
        iframe.decompose()
    cleaned_text = str(soup.encode('utf-8').decode('utf-8'))
    cleaned_text = fix_portuguese_chars(cleaned_text)
    return cleaned_text

def generate_pdf_content(tar_path, extract_dir, course_name):
    extract_tar_gz(tar_path, extract_dir)
    html_dir = os.path.join(extract_dir, 'course', 'drafts', 'html')
    
    sections_before_chapters = ["APRESENTAÇÃO", "INTRODUÇÃO"]
    sections_after_chapters = ["ATIVIDADE EXTRA", "LEITURAS COMPLEMENTARES", "REFERÊNCIAS"]
    chapter_sections = [
        "INTRODUÇÃO DO CAPÍTULO", "CONTEXTUALIZANDO", "CONECTANDO", "APROFUNDANDO",
        "PRATICANDO", "SINTETIZANDO", "RECAPITULANDO", "EXERCITANDO"
    ]
    html_content = []
    processed_sections = set()

    css = """
    <style>
    body { color: #333; margin: 20px; font-family: Arial, sans-serif; }
    h1.chapter-title { 
        font-size: 36px; 
        color: black; 
        margin-bottom: 30px; 
        margin-top: 40px; 
        text-align: center; 
        text-transform: uppercase; 
    }
    h2 { font-size: 20px; color: #0288d1; margin-bottom: 15px; }
    h2.chapter-intro { 
        font-size: 20px; 
        color: #0288d1; 
        margin-bottom: 15px; 
        display: inline-flex; 
        align-items: center; 
        background-color: #e6f0fa; 
        padding: 5px 10px; 
        border-radius: 5px; 
        white-space: nowrap; 
    }
    h2.chapter-intro::before { 
        content: url('https://img.icons8.com/ios-filled/24/0288d1/book.png'); 
        margin-right: 10px; 
    }
    p { 
        line-height: 2.2; 
        margin-bottom: 20px; 
        letter-spacing: 0.5px; 
    }
    .section { 
        page-break-before: auto; 
        page-break-after: auto; 
        page-break-inside: avoid; 
    }
    </style>
    """

    def process_main_section(section_name):
        if section_name in processed_sections:
            logger.info(f"process_main_section: Seção {section_name} já processada, ignorando")
            return
        section_html_path = None
        section_url = f"{BASE_URL}/{course_name}/{section_name.lower().replace(' ', '_')}/index.html"
        for html_file in os.listdir(html_dir):
            if html_file.endswith('.html'):
                file_path = os.path.join(html_dir, html_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    title_text = soup.title.text.upper() if soup.title else ""
                    if section_name in title_text and "CAPITULO" not in title_text:
                        section_html_path = file_path
                        logger.info(f"process_main_section: Encontrado HTML {html_file} para {section_name}")
                        break
        if section_name in ["ATIVIDADE EXTRA", "LEITURAS COMPLEMENTARES"]:
            content = fetch_html_content(section_url)
            if content:
                cleaned_content = clean_html_content(content)
                html_content.append(f'<div class="section">{cleaned_content}</div>')
                processed_sections.add(section_name)
                return
        if section_html_path:
            with open(section_html_path, 'r', encoding='utf-8') as f:
                html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                iframe = soup.find('iframe')
                content = fetch_html_content(iframe['src'] if iframe and 'src' in iframe.attrs else section_url)
                if content:
                    cleaned_content = clean_html_content(content)
                    html_content.append(f'<div class="section">{cleaned_content}</div>')
                    processed_sections.add(section_name)
        else:
            logger.warning(f"process_main_section: Seção {section_name} não encontrada ou sem conteúdo válido")

    def process_chapter_section(chapter_index, section_name):
        if f"CAP{chapter_index}_{section_name}" in processed_sections:
            logger.info(f"process_chapter_section: Seção {section_name} do capítulo {chapter_index} já processada, ignorando")
            return None
        section_html_path = None
        title_key = "INTRODUCAO_CAPITULO" if section_name == "INTRODUÇÃO DO CAPÍTULO" else section_name.replace(' ', '_')
        for html_file in os.listdir(html_dir):
            if html_file.endswith('.html'):
                file_path = os.path.join(html_dir, html_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    title_text = soup.title.text.upper() if soup.title else ""
                    expected_title = f"{course_name.upper()} - CAPITULO{chapter_index} - {title_key}"
                    if expected_title in title_text:
                        section_html_path = file_path
                        logger.info(f"process_chapter_section: Encontrado HTML {html_file} para {section_name} em capítulo {chapter_index}")
                        break
        if section_html_path:
            with open(section_html_path, 'r', encoding='utf-8') as f:
                html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                iframe = soup.find('iframe')
                section_url = iframe['src'] if iframe and 'src' in iframe.attrs else f"{BASE_URL}/{course_name}/capitulo{chapter_index}/{title_key.lower()}/index.html"
                content = fetch_html_content(section_url)
                if content:
                    cleaned_content = clean_html_content(content)
                    # Change the title to "INTRODUÇÃO" if it matches "INTRODUÇÃO DO CAPÍTULO"
                    display_title = "INTRODUÇÃO" if section_name == "INTRODUÇÃO DO CAPÍTULO" else section_name
                    h2_class = 'chapter-intro' if section_name == "INTRODUÇÃO DO CAPÍTULO" else ''
                    processed_sections.add(f"CAP{chapter_index}_{section_name}")
                    return f'<div>{cleaned_content}</div>'
        if section_name == "INTRODUÇÃO DO CAPÍTULO":
            logger.info(f"process_chapter_section: Seção {section_name} não encontrada para capítulo {chapter_index}, considerada opcional")
        return None

    logger.info(f"generate_pdf_content: Iniciando processamento para {course_name}")
    for section in sections_before_chapters:
        process_main_section(section)

    chapter_index = 1
    while True:
        chapter_content = []
        chapter_found = False
        for section in chapter_sections:
            section_html = process_chapter_section(chapter_index, section)
            if section_html:
                chapter_content.append(section_html)
                chapter_found = True
        if not chapter_found:
            logger.info(f"generate_pdf_content: Nenhum conteúdo para capítulo {chapter_index}, encerrando busca")
            break
        if chapter_content:
            html_content.append(f'<div class="section"><h1 class="chapter-title">Capítulo {chapter_index}</h1>{"".join(chapter_content)}</div>')
            logger.info(f"generate_pdf_content: Adicionado capítulo {chapter_index}")
        chapter_index += 1

    for section in sections_after_chapters:
        process_main_section(section)

    full_html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>{course_name}</title>
        {css}
    </head>
    <body>
        {"".join(html_content)}
    </body>
    </html>
    """
    logger.info(f"generate_pdf_content: HTML gerado, tamanho: {len(full_html)} bytes")
    
    return full_html

def generate_pdf(tar_path, course_name):
    extract_dir = os.path.join(settings.TEMP_REQUEST_DIR, 'pdf_extract')
    temp_html_dir = os.path.join(settings.TEMP_REQUEST_DIR, 'temp_html')
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs(temp_html_dir, exist_ok=True)
    html_path = os.path.join(temp_html_dir, f"{course_name}.html")
    pdf_temp_path = os.path.join(temp_html_dir, f"{course_name}.pdf")
    try:
        logger.info(f"generate_pdf: Iniciando geração de PDF para {course_name}")
        full_html = generate_pdf_content(tar_path, extract_dir, course_name)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        logger.info(f"generate_pdf: HTML salvo em {html_path}")
        pdfkit.from_file(html_path, pdf_temp_path, options={'encoding': 'UTF-8'})
        logger.info(f"generate_pdf: PDF salvo em {pdf_temp_path}")
        pdf_buffer = BytesIO()
        with open(pdf_temp_path, 'rb') as f:
            pdf_buffer.write(f.read())
        pdf_buffer.seek(0)
        logger.info(f"generate_pdf: PDF gerado para {course_name}")
        return pdf_buffer
    except Exception as e:
        logger.error(f"generate_pdf: Erro ao gerar PDF: {str(e)}")
        raise
    finally:
        logger.info(f"generate_pdf: Limpando diretórios {extract_dir} e {temp_html_dir}")
        shutil.rmtree(extract_dir, ignore_errors=True)
        shutil.rmtree(temp_html_dir, ignore_errors=True)
