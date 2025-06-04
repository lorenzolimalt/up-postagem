from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import json
from .utils import (
    limpar_pastas, create_assets, create_about_files, create_info_files,
    create_wiki_file, create_policy_structure, create_grading_policy,
    create_assets_json, create_course_xml, create_course_structure,
    compress_course_folder, generate_random_sigla
)
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def generate_course(request):
    """Gera a estrutura .tar.gz com iframes para URLs externas."""
    if request.method != 'POST':
        return HttpResponse(json.dumps({"error": "Método POST requerido"}), content_type="application/json", status=400)

    try:
        data = json.loads(request.body)
        course_name = data.get('course_name')
        org = data.get('org', 'PTEC')
        if not course_name:
            return HttpResponse(json.dumps({"error": "Nome do curso é obrigatório"}), content_type="application/json", status=400)

        temp_request_dir = settings.TEMP_REQUEST_DIR
        output_folder = os.path.join(temp_request_dir, 'course')
        limpar_pastas(output_folder)

        random_sigla = generate_random_sigla()
        course_id_ano = f"2025_{random_sigla}"
        course_id = f"{org}+{random_sigla}+{course_id_ano}"

        create_assets(output_folder)
        create_about_files(output_folder, course_name)
        create_info_files(output_folder)
        create_policy_structure(output_folder, course_name)
        create_grading_policy(output_folder)
        create_assets_json(output_folder)
        create_course_xml(output_folder, org)
        create_wiki_file(output_folder, org, random_sigla, course_id_ano)
        create_course_structure(output_folder, course_name, org, random_sigla, course_id_ano)

        tar_file_path = compress_course_folder(output_folder)
        response = FileResponse(
            open(tar_file_path, 'rb'),
            as_attachment=True,
            filename=f"{course_name}.tar.gz"
        )
        logger.info(f"generate_course: Successfully generated {tar_file_path}")
        return response
    except Exception as e:
        logger.error(f"generate_course: Error: {str(e)}")
        return HttpResponse(json.dumps({"error": str(e)}), content_type="application/json", status=500)