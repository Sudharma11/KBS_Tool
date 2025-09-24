from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from crewai import Crew, Process
import json
import os
import mimetypes
import uuid
import asyncio
import re
from urllib.parse import urlparse
from django.conf import settings

# Corrected: Import the new Agent class for report generation
from BizAgent.reports.report_gen import UrlReportGeneratorAgent
from BizAgent.agents.agents import (
    url_scrapper, url_analyzer, linkedin_agent,
    company_researcher, competitor_analyst, finance_analyst,
    market_analyst, news_gatherer, financial_report_generator
)
# Corrected: Import the new, consolidated linkedin_task
from BizAgent.agents.tasks import (
    url_scrape_task, linkedin_task, url_analyze_task,
    company_task, competitor_task, finance_task, market_task, news_task, 
    generate_financial_task
)
from BizAgent.reports.md_to_Docx import convert_md_to_docx
from BizAgent.prompts.prompt import URL_REPORT_GENERATION_PROMPT
from BizAgent.services.kanini_scraper import run_kanini_scrape_and_update

# --- Helper Functions ---

def _get_company_name(url: str, report_content: str) -> str:
    match = re.search(r'#+\s*(?:Executive Summary|Company Overview|Report for)\s*:\s*([^\n\r]+)', report_content, re.IGNORECASE)
    if match:
        name = match.group(1).strip().replace('*', '').replace('#', '').strip()
        if name: return name
    try:
        hostname = urlparse(url).hostname
        if hostname: return hostname.replace('www.', '').split('.')[0].capitalize()
    except Exception: pass
    return "Target Company"

def _run_secondary_analyses(company_name, ticker_symbol, request_id):
    if not company_name or company_name == "Target Company":
        print("--- Skipping secondary analysis: No specific company name found. ---")
        return None
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    print(f"--- Starting secondary analysis for: {company_name} (Ticker: {ticker_symbol or 'Not Provided'}) ---")
    try:
        sales_intelligence_crew = Crew(
            agents=[
                company_researcher, competitor_analyst, finance_analyst,
                market_analyst, news_gatherer, financial_report_generator
            ],
            tasks=[
                company_task, competitor_task, finance_task,
                market_task, news_task, generate_financial_task
            ],
            process=Process.sequential,
            verbose=True
        )
        
        financial_markdown = sales_intelligence_crew.kickoff(inputs={
            "company_name": company_name,
            "ticker_symbol": ticker_symbol
        })
        
        financial_md_path = os.path.join(settings.MEDIA_ROOT, f"financial_report_{request_id}.md")
        with open(financial_md_path, "w", encoding="utf-8") as f:
            f.write(financial_markdown)

        financial_docx_path = os.path.join(settings.MEDIA_ROOT, f"financial_report_{request_id}.docx")
        convert_md_to_docx(
            md_path=financial_md_path,
            docx_path=financial_docx_path,
            company_name=company_name,
            report_type='financial'
        )
        return financial_docx_path
    except Exception as e:
        print(f"Error during secondary analyses: {e}")
        return None

# --- Main Views ---

@csrf_exempt
@require_POST
def generate_url_report(request):
    try:
        data = json.loads(request.body)
        url = data.get('url')
        ticker_symbol = data.get('ticker_symbol', '')
        linkedin_name = data.get('linkedin_name', '')

        if not url:
            return JsonResponse({"error": "URL is required."}, status=400)
        
        request_id = uuid.uuid4().hex[:8]
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        # Corrected: Use the new, streamlined task list
        url_analysis_crew = Crew(
            agents=[url_scrapper, linkedin_agent, url_analyzer],
            tasks=[url_scrape_task, linkedin_task, url_analyze_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Use a default if linkedin_name is not provided, so the task doesn't fail
        effective_linkedin_name = linkedin_name or urlparse(url).hostname.replace('www.', '').split('.')[0]

        # Corrected: Pass linkedin_name as an input for the new task
        target_report_content = url_analysis_crew.kickoff(inputs={
            "url": url,
            "linkedin_name": effective_linkedin_name
        })
        
        if not target_report_content or "unable to complete" in target_report_content.lower():
             return JsonResponse({"error": "Failed to generate the main analysis report from the URL."}, status=500)

        company_name = _get_company_name(url, target_report_content)

        target_md_path = os.path.join(settings.MEDIA_ROOT, f"target_url_report_{request_id}.md")
        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(target_report_content)
        
        target_docx_path = os.path.join(settings.MEDIA_ROOT, f"target_url_report_{request_id}.docx")
        convert_md_to_docx(target_md_path, target_docx_path, company_name, 'target')

        kanini_txt_path = os.path.join(settings.BASE_DIR, "BizAgent", "Data", "KANINI_SERVICES.txt")
        compare_agent = UrlReportGeneratorAgent()
        comparison_content = compare_agent.run(
            company_doc_path=kanini_txt_path,
            target_company_doc_path=target_md_path,
            prompt_template=URL_REPORT_GENERATION_PROMPT
        )
        
        comparison_md_path = os.path.join(settings.MEDIA_ROOT, f"comparison_url_report_{request_id}.md")
        with open(comparison_md_path, "w", encoding="utf-8") as f:
            f.write(comparison_content)

        comparison_docx_path = os.path.join(settings.MEDIA_ROOT, f"comparison_url_report_{request_id}.docx")
        convert_md_to_docx(comparison_md_path, comparison_docx_path, company_name, 'comparison')
        
        financial_path = _run_secondary_analyses(company_name, ticker_symbol, request_id)

        return JsonResponse({
            "message": "All reports generated successfully.",
            "target_report_file": os.path.basename(target_docx_path),
            "comparison_report_file": os.path.basename(comparison_docx_path),
            "financial_report_file": os.path.basename(financial_path) if financial_path else None,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_POST
def update_kanini_data(request):
    try:
        output_directory = os.path.join(settings.BASE_DIR, "BizAgent", "Data")
        run_kanini_scrape_and_update(output_directory)
        return JsonResponse({"message": "Kanini services data has been updated successfully."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_POST
def upload_pdf(request):
    pdf_file = request.FILES.get('pdf')
    if not pdf_file: return JsonResponse({"error": "No PDF file was uploaded."}, status=400)
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = default_storage.save(os.path.join(upload_dir, pdf_file.name), pdf_file)
    return JsonResponse({"message": "File uploaded successfully.", "pdf_path": file_path})

def url_report_page(request):
    return render(request, "url_report.html")

def download_docx(request, filename):
    if ".." in filename or filename.startswith(("/", "\\")):
        raise Http404("Invalid filename.")
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(file_path):
        raise Http404(f"File not found: {filename}")
    mime_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type=mime_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response



# Other views like generate_linkedin_insights and download_docx remain the same...
# For brevity, they are omitted but should be included in your final views.py


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Other views like generate_linkedin_insights and download_docx remain the same...
# For brevity, they are omitted but should be included in your final views.py



# from django.shortcuts import render
# from django.http import JsonResponse
# from django.http import FileResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# from django.core.files.storage import default_storage
# from crewai import Crew
# import json
# import os

# from django.conf import settings
# from BizAgent.prompts.prompt import URL_REPORT_GENERATION_PROMPT
# from BizAgent.agents.tasks import url_scrape_task, url_analyze_task
# from BizAgent.agents.tasks import pdf_reading_task, pdf_analyze_task, generate_financial_task,linkedin_task
# from BizAgent.agents.agents import financial_report_generator, linkedin_agent
# from BizAgent.reports.financial_report_tool import extract_company_name_from_md
# from BizAgent.reports.md_to_Docx import convert_md_to_docx 
# from BizAgent.reports.report_gen import UrlReportGeneratorAgent,PdfReportGeneratorAgent  
# from BizAgent.reports.merge_docx import merge_reports_to_final

# @csrf_exempt
# @require_POST
# def generate_url_report(request):
#     try:
#         data = json.loads(request.body)
#         url = data.get('url')
#         os.environ["TARGET_URL"] = url
#         cwd = os.getcwd()
#         print(f"Current working directory: {cwd}")
#         # Step 1: Generate target company report
#         crew = Crew(
#             agents=[url_scrape_task.agent, url_analyze_task.agent],
#             tasks=[url_scrape_task, url_analyze_task],
#             verbose=True
#         )

#         result = crew.kickoff(inputs={"url": url})
#         markdown = result.output if hasattr(result, "output") else str(result)

#         # Ensure media directory exists
#         if not os.path.exists("media"):
#             os.makedirs("media")

#         # Save target company report
#         target_md_path = "media/target_company.md"
#         with open(target_md_path, "w", encoding="utf-8") as f:
#             f.write(markdown)

#         target_docx_path = "media/target_company.docx"
#         convert_md_to_docx(target_md_path, target_docx_path)
#         print()
        
#         # Step 2: Generate comparative report
#         cwd = os.getcwd()
#         print(f"Current working directory: {cwd}")
#         kanini_txt_path = r"BizAgent\Data\KANINI_SERVICES.txt"
#         if not os.path.exists(kanini_txt_path):
#             return JsonResponse({"error": "Kanini summary file not found"}, status=500)

#         compare_agent = UrlReportGeneratorAgent()
#         comparison_md_path = compare_agent.run(
#             company_doc_path=kanini_txt_path,
#             target_company_doc_path=target_md_path,
#             prompt_template=URL_REPORT_GENERATION_PROMPT
#         )
    
#         # Optional: Convert comparison report to .docx
#         comparison_docx_path = "media/comparison_report.docx"
#         convert_md_to_docx(comparison_md_path, comparison_docx_path)


#         # Response with both reports
#         return JsonResponse({
#             "message": "URL report and comparison report generated.",
#             "target_docx_path": f"{settings.MEDIA_URL}target_company.docx",
#             "comparison_docx_path": f"{settings.MEDIA_URL}comparison_report.docx"
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
    
# # Generate PDF report and comparison report
# @csrf_exempt
# @require_POST
# def generate_pdf_report(request):
#     try:
#         data = json.loads(request.body)
#         pdf_path = data.get('pdf_path')
#         os.environ["PDF_PATH"] = pdf_path

#         # Step 1: Generate target company report from PDF
#         crew = Crew(
#             agents=[pdf_reading_task.agent, pdf_analyze_task.agent],
#             tasks=[pdf_reading_task, pdf_analyze_task],
#             verbose=True
#         )

#         result = crew.kickoff(inputs={"pdf_path": pdf_path})
#         markdown = result.output if hasattr(result, "output") else str(result)

#         # Ensure media folder exists
#         if not os.path.exists("media"):
#             os.makedirs("media")

#         # Save target report
#         target_md_path = "media/target_company_from_pdf.md"
#         with open(target_md_path, "w", encoding="utf-8") as f:
#             f.write(markdown)

#         target_docx_path = "media/target_company_from_pdf.docx"
#         convert_md_to_docx(target_md_path, target_docx_path)

#         # Step 2: Generate comparison report
#         kanini_txt_path = r"BizInsightAnalyzer\BizBackend\BizAgent\Data\KANINI_SERVICES.txt"
#         if not os.path.exists(kanini_txt_path):
#             return JsonResponse({"error": "Kanini summary file not found"}, status=500)

#         compare_agent = PdfReportGeneratorAgent()
#         comparison_txt_path = compare_agent.run(
#             company_doc_path=kanini_txt_path,
#             target_company_doc_path=target_md_path,
#             prompt_template=URL_REPORT_GENERATION_PROMPT
#         )

#         comparison_docx_path = "media/pdf_comparison_report.docx"
#         convert_md_to_docx(comparison_txt_path, comparison_docx_path)

#         return JsonResponse({
#             "message": "PDF report and comparison report generated.",
#             "target_docx_path": target_docx_path,
#             "comparison_docx_path": comparison_docx_path
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # # Download the generated DOCX report
# # @csrf_exempt
# # @require_POST
# # def download_docx(request):
# #     docx_path = "media/final_report.docx"
# #     if os.path.exists(docx_path):
# #         return FileResponse(open(docx_path, "rb"), as_attachment=True, filename="final_report.docx")
# #     return JsonResponse({"error": "File not found"}, status=404)


# from django.http import FileResponse, JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# from django.conf import settings
# import mimetypes
# from django.http import HttpResponse, Http404

# def download_docx(request, report_type):
#     """
#     Download target or comparison report based on report_type
#     """
#     file_map = {
#         "target": os.path.join(settings.BASE_DIR, "media", "target_company.docx"),
#         "comparison": os.path.join(settings.BASE_DIR, "media", "comparison_report.docx"),
#     }

#     file_path = file_map.get(report_type)
#     if not file_path or not os.path.exists(file_path):
#         raise Http404("File not found")

#     mime_type, _ = mimetypes.guess_type(file_path)
#     with open(file_path, "rb") as f:
#         response = HttpResponse(f.read(), content_type=mime_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
#         response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
#         return response
# # Upload PDF file for processing
# @csrf_exempt
# @require_POST
# def upload_pdf(request):
#     pdf_file = request.FILES.get('pdf')
#     if not pdf_file:
#         return JsonResponse({"error": "No PDF uploaded"}, status=400)

#     file_path = default_storage.save(f"uploads/{pdf_file.name}", pdf_file)
#     return JsonResponse({"message": "Uploaded", "pdf_path": file_path})


# @csrf_exempt
# @require_POST
# def check_file_exists(request):
#     # Hardcoded file path
#     legacy_file_path = os.path.join(settings.BASE_DIR, "url_service_opportunity.md")
#     file_path = legacy_file_path
#     if os.path.exists(file_path):
#         return JsonResponse({"exists": True}, legacy_file_path)
#     else:
#         return JsonResponse({"exists": False})

   
# def url_report_page(request):
#     return render(request, "url_report.html")



# @csrf_exempt
# @require_POST
# def generate_linkedin_insights(request):
#     try:
#         data = json.loads(request.body)
#         universal_name = data.get("universal_name")
#         print("########### Requested company:", universal_name)

#         crew = Crew(
#             agents=[linkedin_agent],
#             tasks=[linkedin_task],
#             verbose=True,
#         )

#         result = crew.kickoff(inputs={"universal_name": universal_name})
#         raw_output = result.output if hasattr(result, "output") else str(result)

#         # --- Clean output (remove accidental fences) ---
#         clean_output = raw_output.strip()
#         if clean_output.startswith("```json"):
#             clean_output = clean_output[7:]
#         if clean_output.endswith("```"):
#             clean_output = clean_output[:-3]
#         clean_output = clean_output.strip()

#         # --- Ensure it's valid JSON ---
#         try:
#             parsed = json.loads(clean_output)
#         except json.JSONDecodeError:
#             print("########### WARNING: Output not valid JSON, wrapping in dict")
#             parsed = {"raw_output": clean_output}

#         # --- Save to file ---
#         if not os.path.exists("media"):
#             os.makedirs("media")

#         report_path = os.path.join("media", "linkedin_insights.json")
#         with open(report_path, "w", encoding="utf-8") as f:
#             json.dump(parsed, f, indent=2, ensure_ascii=False)

#         print("########### Report saved at:", report_path)

#         return JsonResponse({
#             "message": "LinkedIn insights generated.",
#             "report_path": f"{settings.MEDIA_URL}linkedin_insights.json",
#             "output": parsed,  # send parsed JSON
#         })

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return JsonResponse({"error": str(e)}, status=500)