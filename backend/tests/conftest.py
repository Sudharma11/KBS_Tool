import pytest
import asyncio
import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.agents.website_agent import LangGraphCompanyComparator
from app.agents.linkedin_agent import LinkedInAnalysisAgent
from app.agents.financial_agent import FinancialAnalysisAgent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_companies():
    return {
        "company1": {"name": "KANINI", "website": "https://kanini.com/", "linkedin": "https://www.linkedin.com/company/kanini/"},
        "company2": {"name": "Infosys", "website": "https://www.infosys.com/", "linkedin": "https://www.linkedin.com/company/infosys/"},
    }


@pytest.fixture
def mock_gemini_response():
    return {
        "text": json.dumps({
            "company_identity": {"company_name": "Test Company", "website_title": "Test", "meta_description": "Test", "logo_url": ""},
            "business_offerings": {"core_services": ["IT Consulting"], "service_categories": ["Technology"], "key_capabilities": [], "pricing_mentions": []},
        })
    }


@pytest.fixture
def mock_session_data():
    return {"session_id": "test-session-123", "status": "running", "terminal_output": [], "start_time": 1700000000.0}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_analysis_result():
    return {"executive_overview": "Test overview", "full_report": "Test report", "status": "completed"}
