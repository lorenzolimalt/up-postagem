from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import json
from .utils import generate_pdf
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def generate_pdf_view(request):
    """Gera um PDF a partir de um arquivo .tar.gz."""
    if request.method != 'POST':
        return HttpResponse(json.dumps({"error": "Método POST requerido"}), content_type="application/json", status=400)

    try:
        course_name = request.POST.get('course_name')
        tar_file = request.FILES.get('tar_file')
        if not course_name or not tar_file:
            return HttpResponse(json.dumps({"error": "course_name e tar_file são obrigatórios"}), content_type="application/json", status=400)

        # Salvar o arquivo .tar.gz temporariamente
        tar_path = os.path.join(settings.TEMP_REQUEST_DIR, f"{course_name}.tar.gz")
        with open(tar_path, 'wb') as f:
            for chunk in tar_file.chunks():
                f.write(chunk)
        logger.info(f"generate_pdf_view: Arquivo .tar.gz salvo em {tar_path}")

        # Gerar o PDF
        pdf_buffer = generate_pdf(tar_path, course_name)
        response = FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=f"{course_name}.pdf"
        )
        logger.info(f"generate_pdf_view: PDF gerado para {course_name}")
        return response
    except Exception as e:
        logger.error(f"generate_pdf_view: Erro: {str(e)}")
        return HttpResponse(json.dumps({"error": str(e)}), content_type="application/json", status=500)
    finally:
        if os.path.exists(tar_path):
            os.remove(tar_path)