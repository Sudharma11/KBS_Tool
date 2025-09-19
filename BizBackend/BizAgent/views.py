from django.shortcuts import render
from django.http import JsonResponse
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from crewai import Crew
import json
import os

from django.conf import settings
from BizAgent.prompts.prompt import URL_REPORT_GENERATION_PROMPT
from BizAgent.agents.tasks import url_scrape_task, url_analyze_task
from BizAgent.agents.tasks import pdf_reading_task, pdf_analyze_task, generate_financial_task
from BizAgent.agents.agents import financial_report_generator
from BizAgent.reports.financial_report_tool import extract_company_name_from_md
from BizAgent.reports.md_to_Docx import convert_md_to_docx 
from BizAgent.reports.report_gen import UrlReportGeneratorAgent,PdfReportGeneratorAgent  
from BizAgent.reports.merge_docx import merge_reports_to_final

@csrf_exempt
@require_POST
def generate_url_report(request):
    try:
        data = json.loads(request.body)
        url = data.get('url')
        os.environ["TARGET_URL"] = url
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        # Step 1: Generate target company report
        crew = Crew(
            agents=[url_scrape_task.agent, url_analyze_task.agent],
            tasks=[url_scrape_task, url_analyze_task],
            verbose=True
        )

        result = crew.kickoff(inputs={"url": url})
        markdown = result.output if hasattr(result, "output") else str(result)

        # Ensure media directory exists
        if not os.path.exists("media"):
            os.makedirs("media")

        # Save target company report
        target_md_path = "media/target_company.md"
        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        target_docx_path = "media/target_company.docx"
        convert_md_to_docx(target_md_path, target_docx_path)
        print()
        
        # Step 2: Generate comparative report
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        kanini_txt_path = r"BizAgent\Data\KANINI_SERVICES.txt"
        if not os.path.exists(kanini_txt_path):
            return JsonResponse({"error": "Kanini summary file not found"}, status=500)

        compare_agent = UrlReportGeneratorAgent()
        comparison_md_path = compare_agent.run(
            company_doc_path=kanini_txt_path,
            target_company_doc_path=target_md_path,
            prompt_template=URL_REPORT_GENERATION_PROMPT
        )
    
        # Optional: Convert comparison report to .docx
        comparison_docx_path = "media/comparison_report.docx"
        convert_md_to_docx(comparison_md_path, comparison_docx_path)


        # Response with both reports
        return JsonResponse({
            "message": "URL report and comparison report generated.",
            "target_docx_path": f"{settings.MEDIA_URL}target_company.docx",
            "comparison_docx_path": f"{settings.MEDIA_URL}comparison_report.docx"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# Generate PDF report and comparison report
@csrf_exempt
@require_POST
def generate_pdf_report(request):
    try:
        data = json.loads(request.body)
        pdf_path = data.get('pdf_path')
        os.environ["PDF_PATH"] = pdf_path

        # Step 1: Generate target company report from PDF
        crew = Crew(
            agents=[pdf_reading_task.agent, pdf_analyze_task.agent],
            tasks=[pdf_reading_task, pdf_analyze_task],
            verbose=True
        )

        result = crew.kickoff(inputs={"pdf_path": pdf_path})
        markdown = result.output if hasattr(result, "output") else str(result)

        # Ensure media folder exists
        if not os.path.exists("media"):
            os.makedirs("media")

        # Save target report
        target_md_path = "media/target_company_from_pdf.md"
        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        target_docx_path = "media/target_company_from_pdf.docx"
        convert_md_to_docx(target_md_path, target_docx_path)

        # Step 2: Generate comparison report
        kanini_txt_path = r"BizInsightAnalyzer\BizBackend\BizAgent\Data\KANINI_SERVICES.txt"
        if not os.path.exists(kanini_txt_path):
            return JsonResponse({"error": "Kanini summary file not found"}, status=500)

        compare_agent = PdfReportGeneratorAgent()
        comparison_txt_path = compare_agent.run(
            company_doc_path=kanini_txt_path,
            target_company_doc_path=target_md_path,
            prompt_template=URL_REPORT_GENERATION_PROMPT
        )

        comparison_docx_path = "media/pdf_comparison_report.docx"
        convert_md_to_docx(comparison_txt_path, comparison_docx_path)

        return JsonResponse({
            "message": "PDF report and comparison report generated.",
            "target_docx_path": target_docx_path,
            "comparison_docx_path": comparison_docx_path
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# # Download the generated DOCX report
# @csrf_exempt
# @require_POST
# def download_docx(request):
#     docx_path = "media/final_report.docx"
#     if os.path.exists(docx_path):
#         return FileResponse(open(docx_path, "rb"), as_attachment=True, filename="final_report.docx")
#     return JsonResponse({"error": "File not found"}, status=404)


from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import mimetypes
from django.http import HttpResponse, Http404

def download_docx(request, report_type):
    """
    Download target or comparison report based on report_type
    """
    file_map = {
        "target": os.path.join(settings.BASE_DIR, "media", "target_company.docx"),
        "comparison": os.path.join(settings.BASE_DIR, "media", "comparison_report.docx"),
    }

    file_path = file_map.get(report_type)
    if not file_path or not os.path.exists(file_path):
        raise Http404("File not found")

    mime_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type=mime_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
# Upload PDF file for processing
@csrf_exempt
@require_POST
def upload_pdf(request):
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({"error": "No PDF uploaded"}, status=400)

    file_path = default_storage.save(f"uploads/{pdf_file.name}", pdf_file)
    return JsonResponse({"message": "Uploaded", "pdf_path": file_path})


@csrf_exempt
@require_POST
def check_file_exists(request):
    # Hardcoded file path
    legacy_file_path = os.path.join(settings.BASE_DIR, "url_service_opportunity.md")
    file_path = legacy_file_path
    if os.path.exists(file_path):
        return JsonResponse({"exists": True}, legacy_file_path)
    else:
        return JsonResponse({"exists": False})

   
def url_report_page(request):
    return render(request, "url_report.html")
