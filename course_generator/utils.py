import os
import uuid
import tarfile
import shutil
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

BASE_URL = "https://pdinfinita.com/googledrive/PTEC"

def check_url_exists(url):
    """Verifica se a URL existe (status 200)."""
    try:
        response = requests.head(url, timeout=30, verify=False)
        exists = response.status_code == 200
        logger.debug(f"check_url_exists: URL {url} exists: {exists}")
        return exists
    except requests.RequestException as e:
        logger.warning(f"check_url_exists: Error checking URL {url}: {str(e)}")
        return False

def generate_iframe_html(course_name, section_or_chapter, theme_or_section):
    """Gera HTML com iframe apontando para a URL externa."""
    if theme_or_section:
        url = f"{BASE_URL}/{course_name}/{section_or_chapter}/{theme_or_section}/index.html"
    else:
        url = f"{BASE_URL}/{course_name}/{section_or_chapter}/index.html"
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{course_name} - {section_or_chapter} - {theme_or_section}</title>
</head>
<body>
    <p></p>
    <p></p>
    <p><iframe width="100%" style="min-height: 600px !important;" src="{url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen=""></iframe></p>
</body>
</html>"""
    return html_content

def limpar_pastas(*pastas):
    """Remove e recria pastas."""
    for pasta in pastas:
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
        os.makedirs(pasta, exist_ok=True)

def create_assets(base_path):
    """Cria pasta e arquivo assets.xml."""
    assets_path = os.path.join(base_path, 'assets')
    os.makedirs(assets_path, exist_ok=True)
    with open(os.path.join(assets_path, 'assets.xml'), 'w', encoding='utf-8') as f:
        f.write('<assets/>')

def create_about_files(base_path, course_name):
    """Cria arquivos about."""
    about_path = os.path.join(base_path, 'about')
    os.makedirs(about_path, exist_ok=True)
    overview_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Visão Geral do Curso</title>
    </head>
    <body>
        <h1>{course_name}</h1>
        <p>Este curso aborda os fundamentos e práticas.</p>
    </body>
    </html>
    """
    with open(os.path.join(about_path, 'overview.html'), 'w', encoding='utf-8') as f:
        f.write(overview_content)
    short_description = f"<p>Curso sobre {course_name}.</p>"
    with open(os.path.join(about_path, 'short_description.html'), 'w', encoding='utf-8') as f:
        f.write(short_description)

def create_info_files(base_path):
    """Cria arquivos info."""
    info_path = os.path.join(base_path, 'info')
    os.makedirs(info_path, exist_ok=True)
    with open(os.path.join(info_path, 'info.xml'), 'w', encoding='utf-8') as f:
        f.write('<info/>')

def create_wiki_file(base_path, org, random_sigla, course_id_ano):
    """Cria arquivo wiki."""
    wiki_path = os.path.join(base_path, 'wiki')
    os.makedirs(wiki_path, exist_ok=True)
    wiki_slug = f"{org}+{random_sigla}+{course_id_ano}"
    wiki_content = f'<wiki slug="{wiki_slug}"/>'
    with open(os.path.join(wiki_path, f"{wiki_slug}.xml"), 'w', encoding='utf-8') as f:
        f.write(wiki_content)

def create_policy_structure(base_path, course_name):
    """Cria estrutura de políticas."""
    policies_path = os.path.join(base_path, 'policies', '2025_T4')
    os.makedirs(policies_path, exist_ok=True)
    static_course_path = os.path.join(base_path, 'static')
    os.makedirs(static_course_path, exist_ok=True)
    policy_data = {
        "course/2025_T4": {
            "cert_html_view_enabled": True,
            "course_image": "placeholder.png",
            "discussion_topics": {"Geral": {"id": "course"}},
            "discussions_settings": {
                "enable_graded_units": False,
                "enable_in_context": True,
                "provider_type": "openedx",
                "unit_level_visibility": True
            },
            "display_name": course_name,
            "enable_timed_exams": True,
            "minimum_grade_credit": 0.8,
            "language": "pt",
            "pdf_textbooks": [
                {"chapters": [{"title": "Capitulo1", "url": "/static/placeholder.pdf"}],
                 "id": "3PDF_TEXTO_LIVRO", "tab_title": "livro do estudante OFF"}
            ],
            "start": "2025-01-01T00:00:00Z",
            "tabs": [
                {"course_staff_only": False, "name": "Course", "type": "courseware"},
                {"course_staff_only": False, "name": "Progress", "type": "progress"},
                {"course_staff_only": False, "name": "Dates", "type": "dates"},
                {"course_staff_only": False, "name": "Discussion", "type": "discussion"},
                {"course_staff_only": False, "name": "Wiki", "type": "wiki"},
                {"course_staff_only": False, "name": "Textbooks", "type": "textbooks"},
                {"course_staff_only": False, "name": "Textbooks", "type": "pdf_textbooks"}
            ]
        }
    }
    with open(os.path.join(policies_path, 'policy.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(policy_data, f, indent=4)

def create_grading_policy(base_path):
    """Cria política de avaliação."""
    policies_path = os.path.join(base_path, 'policies', '2025_T4')
    os.makedirs(policies_path, exist_ok=True)
    grading_policy = {
        "GRADER": [
            {"drop_count": 2, "min_count": 12, "short_label": "HW", "type": "Homework", "weight": 0.15},
            {"drop_count": 2, "min_count": 12, "type": "Lab", "weight": 0.15},
            {"drop_count": 0, "min_count": 1, "short_label": "Midterm", "type": "Midterm Exam", "weight": 0.3},
            {"drop_count": 0, "min_count": 1, "short_label": "Final", "type": "Final Exam", "weight": 0.4}
        ],
        "GRADE_CUTOFFS": {"Pass": 0.5}
    }
    with open(os.path.join(policies_path, 'grading_policy.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(grading_policy, f, indent=4)

def create_assets_json(base_path):
    """Cria assets.json."""
    policies_path = os.path.join(base_path, 'policies')
    os.makedirs(policies_path, exist_ok=True)
    with open(os.path.join(policies_path, 'assets.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump({}, f)

def create_course_xml(base_path, org):
    """Cria course.xml."""
    with open(os.path.join(base_path, 'course.xml'), 'w', encoding='utf-8') as f:
        f.write(f'<course url_name="2025_T4" org="{org}" course="TU104"/>')

def create_course_structure(base_path, course_name, org, random_sigla, course_id_ano):
    """Cria a estrutura do curso com iframes para URLs externas existentes."""
    logger.info("create_course_structure: Starting course structure creation")
    course_path = os.path.join(base_path, 'course')
    chapters_path = os.path.join(base_path, 'chapter')
    drafts_path = os.path.join(base_path, 'drafts')
    html_path = os.path.join(drafts_path, 'html')
    vertical_path = os.path.join(drafts_path, 'vertical')
    sequential_path = os.path.join(base_path, 'sequential')
    for path in [course_path, chapters_path, drafts_path, html_path, vertical_path, sequential_path]:
        os.makedirs(path, exist_ok=True)
        logger.info(f"create_course_structure: Created directory {path}")

    main_sections_order = ["apresentação", "sumário", "introdução", "atividade_extra", "leituras_complementares", "referências"]
    themes = ["introducao_capitulo", "contextualizando", "conectando", "aprofundando", "sintetizando", "praticando", "recapitulando", "exercitando"]
    all_sections = []
    chapter_counter = 0
    section_counter = 0

    # Processar seções principais dinamicamente
    for main_section in main_sections_order:
        url = f"{BASE_URL}/{course_name}/{main_section}/index.html"
        if not check_url_exists(url):
            logger.info(f"create_course_structure: Skipping {main_section} - URL does not exist: {url}")
            continue

        section_counter += 1
        section_id = str(uuid.uuid4())
        unique_id = f"section{section_counter:02d}-{uuid.uuid4().hex}"
        section_name = main_section.upper().replace('_', ' ')

        # Criar XML do capítulo
        with open(os.path.join(chapters_path, f"{section_id}.xml"), 'w', encoding='utf-8') as f:
            f.write(f'<chapter display_name="{section_name}" url_name="{section_id}">\n')
            f.write(f'    <sequential url_name="{unique_id}"/>\n')
            f.write('</chapter>\n')
        logger.info(f"create_course_structure: Created chapter XML for {section_name}")

        # Gerar HTML com iframe, passando theme_or_section vazio
        html_content = generate_iframe_html(course_name, main_section, "")
        html_id = f"01-{uuid.uuid4().hex}"
        with open(os.path.join(html_path, f"{html_id}.html"), 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"create_course_structure: Wrote HTML file for {section_name}")

        # Criar XML para a seção HTML
        with open(os.path.join(html_path, f"{html_id}.xml"), "w", encoding='utf-8') as f:
            f.write(f'<html filename="{html_id}" display_name="{section_name}"/>')
        logger.info(f"create_course_structure: Created HTML XML for {section_name}")

        # Criar vertical
        vertical_id = f"01-{uuid.uuid4().hex}"
        vertical_content = f'''
<vertical display_name="{section_name}" parent_url="block-v1:{org}+{random_sigla}+{course_id_ano}+type@sequential+block@{unique_id}" index_in_children_list="0">
<html url_name="{html_id}"/>
</vertical>
'''
        with open(os.path.join(vertical_path, f"{vertical_id}.xml"), 'w', encoding='utf-8') as f:
            f.write(vertical_content)
        logger.info(f"create_course_structure: Created vertical XML for {section_name}")

        # Criar sequential
        with open(os.path.join(sequential_path, f"{unique_id}.xml"), 'w', encoding='utf-8') as f:
            f.write(f'<sequential display_name="{section_name}">\n')
            f.write(f'  <vertical url_name="{vertical_id}" display_name="{section_name}"/>\n')
            f.write('</sequential>')
        logger.info(f"create_course_structure: Created sequential XML for {section_name}")

        chapter_number = {
            "apresentacao": -3, "sumario": -2, "introducao": -1,
            "atividade_extra": 9998, "leituras_complementares": 9997, "referencias": 9999
        }.get(main_section, 0)
        all_sections.append((section_id, chapter_number, section_name))

    # Processar capítulos dinamicamente
    chapter_index = 1
    while True:
        chapter = f"capitulo{chapter_index}"
        # Verificar se pelo menos um tema existe para o capítulo
        chapter_has_content = False
        for theme in themes:
            theme_url = f"{BASE_URL}/{course_name}/{chapter}/{theme}/index.html"
            if check_url_exists(theme_url):
                chapter_has_content = True
                logger.info(f"create_course_structure: Found valid theme {theme} for {chapter}")
                break

        if not chapter_has_content:
            logger.info(f"create_course_structure: No valid themes found, stopping at {chapter}")
            break

        section_counter += 1
        section_id = str(uuid.uuid4())
        unique_id = f"section{section_counter:02d}-{uuid.uuid4().hex}"
        chapter_counter += 1
        section_name = f"Capítulo {chapter_counter}"

        # Criar XML do capítulo
        with open(os.path.join(chapters_path, f"{section_id}.xml"), 'w', encoding='utf-8') as f:
            f.write(f'<chapter display_name="{section_name}" url_name="{section_id}">\n')
            f.write(f'    <sequential url_name="{unique_id}"/>\n')
            f.write('</chapter>\n')
        logger.info(f"create_course_structure: Created chapter XML for {section_name}")

        vertical_ids = []
        # Processar temas dinamicamente
        for unit_index, theme in enumerate(themes, start=0):
            theme_url = f"{BASE_URL}/{course_name}/{chapter}/{theme}/index.html"
            if not check_url_exists(theme_url):
                logger.info(f"create_course_structure: Skipping {theme} in {chapter} - URL does not exist: {theme_url}")
                continue

            html_content = generate_iframe_html(course_name, chapter, theme)
            html_id = f"0{unit_index}-{uuid.uuid4().hex}"
            with open(os.path.join(html_path, f"{html_id}.html"), 'w', encoding='utf-8') as f:
                f.write(html_content)
            with open(os.path.join(html_path, f"{html_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f'<html filename="{html_id}" display_name="{theme.upper()}"/>')
            vertical_id = f"0{unit_index}-{uuid.uuid4().hex}"
            vertical_content = f'''
<vertical display_name="{theme.upper()}" parent_url="block-v1:{org}+{random_sigla}+{course_id_ano}+type@sequential+block@{unique_id}" index_in_children_list="{unit_index}">
<html url_name="{html_id}"/>
</vertical>
'''
            with open(os.path.join(vertical_path, f"{vertical_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(vertical_content)
            vertical_ids.append((vertical_id, theme.upper(), unit_index))
            logger.info(f"create_course_structure: Created vertical for {theme} in {section_name}")

        # Criar sequential
        sequential_content = f'<sequential display_name="{section_name}">\n'
        for vertical_id, display_name, index in sorted(vertical_ids, key=lambda x: x[2]):
            sequential_content += f'  <vertical url_name="{vertical_id}" display_name="{display_name}"/>\n'
        sequential_content += '</sequential>'
        with open(os.path.join(sequential_path, f"{unique_id}.xml"), 'w', encoding='utf-8') as f:
            f.write(sequential_content)
        logger.info(f"create_course_structure: Created sequential XML for {section_name}")

        all_sections.append((section_id, chapter_counter, section_name))
        chapter_index += 1

    # Ordenar seções e criar course XML
    all_sections.sort(key=lambda x: x[1])
    sections_xml = ""
    for section_id, section_number, section_name in all_sections:
        sections_xml += f' <chapter url_name="{section_id}"/>\n'
    course_content = f'<course>\n{sections_xml} <wiki slug="{org}+{random_sigla}+{course_id_ano}"/>\n</course>'
    with open(os.path.join(course_path, '2025_T4.xml'), 'w', encoding='utf-8') as f:
        f.write(course_content)
    logger.info(f"create_course_structure: Created course XML")

def compress_course_folder(base_path):
    """Compacta a pasta em um arquivo .tar.gz."""
    try:
        tar_file_path = f"{base_path}.tar.gz"
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(base_path, arcname=os.path.basename(base_path))
        if os.path.exists(tar_file_path):
            logger.info(f"compress_course_folder: Successfully created {tar_file_path}")
            return tar_file_path
        else:
            raise Exception(f"Arquivo tar.gz não encontrado: {tar_file_path}")
    except Exception as e:
        logger.error(f"compress_course_folder: Error: {str(e)}")
        raise Exception(f"Erro ao compactar a pasta: {str(e)}")

def generate_random_sigla(length=5):
    """Gera uma sigla aleatória."""
    import string
    import random
    return ''.join(random.choices(string.ascii_uppercase, k=length))