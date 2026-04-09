from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import sys
import os
import time
import uuid
from typing import Dict

from app.models.schemas import ComparisonRequest
from app.services.leader_search import process_browser_style_search

router = APIRouter()

# In-memory session store
analysis_sessions: Dict[str, Dict] = {}

# ---------------------------------------------------------------------------
# Kanini hardcoded leaders (used when company1 == KANINI)
# ---------------------------------------------------------------------------
KANINI_LEADERS = [
    {'Name': 'Rakesh Talreja', 'Role': 'SVP - Healthcare Business Unit Leader', 'LinkedinURL': 'https://www.linkedin.com/in/rakesh-b-talreja/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2022/07/Kanini-Rakesh-Talreja.jpg'},
    {'Name': 'Raj Aduma', 'Role': 'Chief Delivery Officer', 'LinkedinURL': 'https://www.linkedin.com/in/adumaraj/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-Raj-Aduma.jpg'},
    {'Name': 'Babu Krishnasamy', 'Role': 'President/CEO', 'LinkedinURL': 'https://www.linkedin.com/in/babu-krishnasamy-25197b6/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-Babu-Team.jpg'},
    {'Name': 'Arunachalam Sundaresan', 'Role': 'Chief Commercial Officer', 'LinkedinURL': 'https://www.linkedin.com/in/aruns/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2021/03/Kanini-Arun-Team.jpg'},
    {'Name': 'Anand Subramaniam', 'Role': 'Chief Solutions Officer, Data Analytics & AI', 'LinkedinURL': 'https://www.linkedin.com/in/anand-sivaraman-subramaniam-7982b5a/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2021/07/Kanini-Anand-Team.jpg'},
    {'Name': 'Sudha Ganesh', 'Role': 'Chief Transformation Officer', 'LinkedinURL': 'https://www.linkedin.com/in/sudha-ganesh-2b478088/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/11/Kanini-Sudha-Team-1.jpg'},
    {'Name': 'Muthiah Natarajan', 'Role': 'Chief Strategy and Growth Officer', 'LinkedinURL': 'https://www.linkedin.com/in/muthiahnatarajan/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2021/02/Kanini-Muthiah-Team.jpg'},
    {'Name': 'Srini Karunakaran', 'Role': 'Chief Operating Officer & Chief Financial Officer', 'LinkedinURL': 'https://www.linkedin.com/in/srinivasankarunakaran/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-Srini-Team.jpg'},
    {'Name': 'Dean Clark', 'Role': 'Executive Vice President - Customer Success', 'LinkedinURL': 'https://www.linkedin.com/in/dean-clark-leadership-mentor/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2024/05/clark_dean-kanini-teams.jpg'},
    {'Name': 'Robert Claypool', 'Role': 'Head of Product Engineering', 'LinkedinURL': 'https://www.linkedin.com/in/robertclaypool/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-Robert-Team.jpg'},
    {'Name': 'David Greene', 'Role': 'Chief Technology Officer', 'LinkedinURL': 'https://www.linkedin.com/in/davidgreene4/', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-David-Green.jpg'},
    {'Name': 'Nileen Gohel', 'Role': 'Chief Program Management Officer', 'LinkedinURL': 'https://www.linkedin.com/in/nileengohel', 'ImageURL': 'https://kanini.com/wp-content/uploads/2020/07/Kanini-Nileen-Gohel.jpg'},
]

REPORTS_DIR = "reports"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class PrintCapture:
    """Captures stdout and streams lines into the session's terminal_output."""
    def __init__(self, session_id: str):
        self.session_id = session_id

    def write(self, text: str):
        if text.strip():
            for line in text.strip().split('\n'):
                if line.strip():
                    formatted = f"[{time.strftime('%H:%M:%S')}] {line.strip()}"
                    if self.session_id in analysis_sessions:
                        analysis_sessions[self.session_id]['terminal_output'].append(formatted)

    def flush(self):
        pass


class MockAnalysis:
    """Fallback demo content when API quota is exceeded."""

    @staticmethod
    def executive_overview(company1: str, company2: str) -> str:
        return f"""
EXECUTIVE OVERVIEW - DEMO MODE
==============================
This analysis compares {company1} and {company2} using comprehensive business intelligence.

KEY FINDINGS:
• Digital Presence: Both companies show active online engagement
• Financial Health: Stable performance indicators observed
• Growth Potential: Positive market positioning

Note: Running in demo mode due to API limits.
"""

    @staticmethod
    def full_report(company1: str, company2: str) -> str:
        return f"""
COMPREHENSIVE COMPANY COMPARISON REPORT - DEMO MODE
====================================================
Analysis Date: {time.strftime("%Y-%m-%d %H:%M:%S")}
Companies: {company1} vs {company2}

Note: This is a demo report. Full analysis requires API quota refresh or upgrade.
"""


def _read_docx_text(filepath: str) -> str:
    from docx import Document
    doc = Document(filepath)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


def _log(session_id: str, message: str):
    analysis_sessions[session_id]['terminal_output'].append(
        f"[{time.strftime('%H:%M:%S')}] {message}"
    )


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

def run_analysis_in_background(session_id: str, request: ComparisonRequest):
    old_stdout = sys.stdout
    sys.stdout = PrintCapture(session_id)

    try:
        _log(session_id, f"Starting analysis: {request.company1_name} vs {request.company2_name}")
        _log(session_id, "Using predefined Kanini data" if request.use_predefined_data else "Scraping fresh data")
        _log(session_id, "Importing analysis modules...")

        from app.services.comparison_workflow import run_unified_comparison

        _log(session_id, "Modules imported - starting workflow...")

        result = run_unified_comparison(
            company1_name=request.company1_name,
            company2_name=request.company2_name,
            company1_website=request.company1_website,
            company2_website=request.company2_website,
            company1_linkedin=request.company1_linkedin,
            company2_linkedin=request.company2_linkedin,
            session_id=session_id,
            use_predefined_data=request.use_predefined_data,
            api_key=request.api_key or None,
            model=request.model or None,
        )
        analysis_sessions[session_id]['result'] = result

        # --- Leadership scraping ---
        _log(session_id, f"Searching for {request.company1_name} leadership...")
        company1_leaders = (
            KANINI_LEADERS if request.company1_name == "KANINI"
            else process_browser_style_search(request.company1_name, request.company1_website)
        )
        analysis_sessions[session_id]['company1_leaders'] = company1_leaders
        _log(session_id, f"Found {len(company1_leaders)} leaders for {request.company1_name}")

        _log(session_id, f"Searching for {request.company2_name} leadership...")
        company2_leaders = process_browser_style_search(request.company2_name, request.company2_website)
        analysis_sessions[session_id]['company2_leaders'] = company2_leaders
        _log(session_id, f"Found {len(company2_leaders)} leaders for {request.company2_name}")

        # --- Read generated reports ---
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_map = {
            'full_report':      f"unified_company_comparison_report_{session_id}.docx",
            'website_report':   f"website_final_report_{session_id}.docx",
            'linkedin_report':  f"linkedin_final_report_{session_id}.docx",
            'financial_report': f"financial_final_report_{session_id}.docx",
        }
        for key, filename in report_map.items():
            filepath = os.path.join(REPORTS_DIR, filename)
            if os.path.exists(filepath):
                analysis_sessions[session_id][key] = _read_docx_text(filepath)
                _log(session_id, f"Report loaded: {filename}")
            else:
                analysis_sessions[session_id][key] = "Report file not generated."
                _log(session_id, f"Report not found: {filename}")

        # --- Load individual reports ---
        analysis_sessions[session_id]['website_company1_report'] = "Kanini is a digital transformation enabler providing cutting-edge software services and solutions. Specializes in Agile Software Development, Cloud Computing, Data Science, and AI. Headquarters in Nashville, Tennessee, with 501-1,000 employees."
        analysis_sessions[session_id]['linkedin_company1_report'] = "Kanini maintains an active LinkedIn presence with focus on thought leadership in digital transformation. Features content on AI, cloud services, and healthcare solutions. Strong employer branding with emphasis on innovation and collaboration."
        analysis_sessions[session_id]['financial_company1_report'] = "Kanini demonstrates strong financial health with efficient operations and growth potential. Revenue model focused on software services and digital solutions. Maintains competitive positioning in the technology sector."
        analysis_sessions[session_id]['website_company2_report'] = result.get("website_company2_report", "No individual website report available")
        analysis_sessions[session_id]['linkedin_company2_report'] = result.get("linkedin_company2_report", "No individual LinkedIn report available")
        analysis_sessions[session_id]['financial_company2_report'] = result.get("financial_company2_report", "No individual financial report available")

        analysis_sessions[session_id]['status'] = 'completed'
        _log(session_id, "Analysis completed successfully!")

    except Exception as e:
        import traceback
        full_error = traceback.format_exc()
        _log(session_id, f"Error: {str(e)}")
        _log(session_id, f"Traceback: {full_error[:500]}")
        if "quota" in str(e).lower() or "429" in str(e):
            analysis_sessions[session_id]['status'] = 'demo_mode'
            analysis_sessions[session_id]['executive_overview'] = MockAnalysis.executive_overview(
                request.company1_name, request.company2_name)
            analysis_sessions[session_id]['full_report'] = MockAnalysis.full_report(
                request.company1_name, request.company2_name)
            analysis_sessions[session_id]['message'] = "API quota exceeded. Showing demo analysis."
            _log(session_id, "Switched to demo mode")
        else:
            analysis_sessions[session_id]['status'] = 'error'
            analysis_sessions[session_id]['error'] = str(e)
    finally:
        sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/run-comparison")
async def run_comparison(request: ComparisonRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    analysis_sessions[session_id] = {
        'status': 'running',
        'terminal_output': [],
        'start_time': time.time(),
        'request': request.dict(),
    }
    _log(session_id, f"Session started: {session_id}")
    _log(session_id, f"Comparing: {request.company1_name} vs {request.company2_name}")
    background_tasks.add_task(run_analysis_in_background, session_id, request)
    return {"status": "started", "session_id": session_id, "message": "Analysis started in background"}


@router.post("/resolve-linkedin-url")
async def resolve_linkedin_url(request: dict):
    linkedin_name = request.get("linkedin_name")
    if not linkedin_name:
        raise HTTPException(status_code=400, detail="Company name is required")
    try:
        from app.services.linkedin_resolver import find_linkedin_company_url_final
        result = find_linkedin_company_url_final({"company_name": linkedin_name, "website": request.get("website", "")})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve LinkedIn URL: {str(e)}")


@router.get("/analysis-status/{session_id}")
async def get_analysis_status(session_id: str):
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = analysis_sessions[session_id]
    response = {
        "status": session['status'],
        "terminal_output": session.get('terminal_output', []),
        "start_time": session['start_time'],
        "current_time": time.time(),
        "duration": round(time.time() - session['start_time'], 2),
    }
    if session['status'] in ['completed', 'demo_mode']:
        response.update({
            "executive_overview": session.get('executive_overview', ''),
            "full_report": session.get('full_report', ''),
            "website_report": session.get('website_report', ''),
            "linkedin_report": session.get('linkedin_report', ''),
            "financial_report": session.get('financial_report', ''),
            "website_company1_report": session.get('website_company1_report', ''),
            "linkedin_company1_report": session.get('linkedin_company1_report', ''),
            "financial_company1_report": session.get('financial_company1_report', ''),
            "website_company2_report": session.get('website_company2_report', ''),
            "linkedin_company2_report": session.get('linkedin_company2_report', ''),
            "financial_company2_report": session.get('financial_company2_report', ''),
            "company1_leaders": session.get('company1_leaders', []),
            "company2_leaders": session.get('company2_leaders', []),
            "company1_name": session.get('request', {}).get('company1_name', ''),
            "company2_name": session.get('request', {}).get('company2_name', ''),
            "message": session.get('message', 'Analysis completed successfully'),
        })
    elif session['status'] == 'error':
        response['error'] = session.get('error', 'Unknown error occurred')
    return response


@router.get("/terminal-output/{session_id}")
async def get_terminal_output(session_id: str, last_index: int = 0):
    if session_id not in analysis_sessions:
        return {"lines": [], "last_index": 0, "status": "not_found"}
    session = analysis_sessions[session_id]
    lines = session.get('terminal_output', [])
    return {
        "lines": lines[last_index:],
        "last_index": len(lines),
        "has_more": last_index < len(lines),
        "status": session['status'],
        "total_lines": len(lines),
    }


@router.get("/download-report/{session_id}/{report_type}")
async def download_report(session_id: str, report_type: str):
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    filename_map = {
        "full":      f"unified_company_comparison_report_{session_id}.docx",
        "website":   f"website_final_report_{session_id}.docx",
        "linkedin":  f"linkedin_final_report_{session_id}.docx",
        "financial": f"financial_final_report_{session_id}.docx",
    }
    if report_type not in filename_map:
        raise HTTPException(status_code=400, detail="Invalid report type")
    filepath = os.path.join(REPORTS_DIR, filename_map[report_type])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"{filepath} not found")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename_map[report_type],
    )


@router.get("/session-terminal-logs/{session_id}")
async def get_session_terminal_logs(session_id: str):
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = analysis_sessions[session_id]
    logs = session.get('terminal_output', [])
    return {"session_id": session_id, "status": session['status'], "total_lines": len(logs), "logs": logs}


@router.get("/cleanup-sessions")
async def cleanup_old_sessions():
    current_time = time.time()
    to_remove = [sid for sid, s in analysis_sessions.items() if current_time - s['start_time'] > 3600]
    for sid in to_remove:
        del analysis_sessions[sid]
    return {"cleaned_sessions": len(to_remove), "remaining_sessions": len(analysis_sessions)}
