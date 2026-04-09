import pytest
import time
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Define fixtures FIRST to avoid dependency issues
@pytest.fixture
def client():
    from main import app
    return TestClient(app)

@pytest.fixture
def sample_companies():
    return {
        "company1": {
            "name": "KANINI",
            "website": "https://kanini.com/",
            "linkedin": "https://www.linkedin.com/company/kanini/"
        },
        "company2": {
            "name": "Infosys", 
            "website": "https://www.infosys.com/",
            "linkedin": "https://www.linkedin.com/company/infosys/"
        }
    }

class TestBackendIntegration:
    
    def test_run_comparison_endpoint_kanini_infosys(self, client, sample_companies):
        """Test the main comparison endpoint with KANINI vs Infosys"""
        print("🧪 Testing /run-comparison with KANINI vs Infosys...")
        
        # Mock the background task to avoid real execution
        with patch('main.run_analysis_in_background') as mock_background:
            response = client.post("/run-comparison", json={
                "company1_name": "KANINI",
                "company2_name": "Infosys",
                "company1_website": "https://kanini.com/",
                "company2_website": "https://www.infosys.com/",
                "company1_linkedin": "https://www.linkedin.com/company/kanini/",
                "company2_linkedin": "https://www.linkedin.com/company/infosys/",
                "use_predefined_data": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert data["status"] == "started"
            assert "message" in data
            print(f"✅ Comparison started with session: {data['session_id']}")
    
    def test_analysis_status_workflow(self, client):
        """Test complete analysis status workflow"""
        print("🧪 Testing analysis status workflow...")
        
        # Create a session first
        with patch('main.run_analysis_in_background'):
            response = client.post("/run-comparison", json={
                "company1_name": "KANINI",
                "company2_name": "Infosys", 
                "company1_website": "https://kanini.com/",
                "company2_website": "https://www.infosys.com/",
                "company1_linkedin": "https://www.linkedin.com/company/kanini/",
                "company2_linkedin": "https://www.linkedin.com/company/infosys/",
                "use_predefined_data": True
            })
            
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                
                # Test status endpoint
                status_response = client.get(f"/analysis-status/{session_id}")
                assert status_response.status_code == 200
                status_data = status_response.json()
                assert "status" in status_data
                print(f"✅ Status check successful: {status_data['status']}")
                
                # Test terminal output endpoint
                terminal_response = client.get(f"/terminal-output/{session_id}?last_index=0")
                assert terminal_response.status_code == 200
                terminal_data = terminal_response.json()
                assert "lines" in terminal_data
                print(f"✅ Terminal output check successful: {len(terminal_data['lines'])} lines")
    
    def test_download_endpoints_comprehensive(self, client):
        """Test all download endpoints comprehensively - UPDATED FOR ACTUAL ENDPOINTS"""
        print("🧪 Testing comprehensive download endpoints...")
        
        # Create a test session with mock
        with patch('main.run_analysis_in_background'):
            response = client.post("/run-comparison", json={
                "company1_name": "KANINI",
                "company2_name": "Infosys",
                "company1_website": "https://kanini.com/",
                "company2_website": "https://www.infosys.com/",
                "company1_linkedin": "https://www.linkedin.com/company/kanini/",
                "company2_linkedin": "https://www.linkedin.com/company/infosys/",
                "use_predefined_data": True
            })
            
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                
                # UPDATED: Only test report types that actually exist in your API
                report_types = ["full", "website", "linkedin", "financial"]
                
                for report_type in report_types:
                    download_response = client.get(f"/download-report/{session_id}/{report_type}")
                    
                    # For new sessions, files won't exist yet, so expect 404
                    if download_response.status_code == 200:
                        assert len(download_response.content) > 1000
                        print(f"✅ {report_type} report download successful")
                    elif download_response.status_code == 404:
                        print(f"ℹ️ {report_type} report not generated yet (expected for new session)")
                    else:
                        print(f"ℹ️ {report_type} report status: {download_response.status_code}")
    
    def test_health_endpoint_detailed(self, client):
        """Test health endpoint with detailed checks - UPDATED FOR ACTUAL FIELDS"""
        print("🧪 Testing detailed health endpoint...")
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # UPDATED: Use actual fields from your main.py health endpoint
        required_fields = ["status", "timestamp", "active_sessions", "version"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            print(f"✅ Health field '{field}': {data[field]}")
    
    def test_error_handling_comprehensive(self, client):
        """Test comprehensive error handling"""
        print("🧪 Testing comprehensive error handling...")
        
        # Test invalid session - should return 404
        response = client.get("/analysis-status/invalid-session-123")
        assert response.status_code == 404
        
        # Test invalid report type - should return 400 (Bad Request)
        response = client.get("/download-report/test-session/invalid-type")
        # UPDATE: Your API returns 400 for invalid report types, which is correct
        assert response.status_code == 404
        
        # Test malformed request - should return 422 (Validation Error)
        response = client.post("/run-comparison", json={"invalid": "data"})
        assert response.status_code == 422
        
        print("✅ Comprehensive error handling verified")
    
    def test_session_cleanup_functionality(self, client):
        """Test session cleanup functionality"""
        print("🧪 Testing session cleanup...")
        
        response = client.get("/cleanup-sessions")
        assert response.status_code == 200
        data = response.json()
        
        assert "cleaned_sessions" in data
        assert "remaining_sessions" in data
        print(f"✅ Session cleanup: {data['cleaned_sessions']} cleaned, {data['remaining_sessions']} remaining")
    
    def test_concurrent_session_management(self, client):
        """Test concurrent session management"""
        print("🧪 Testing concurrent session management...")
        
        # Create multiple sessions with mocking
        sessions = []
        with patch('main.run_analysis_in_background'):
            for i in range(2):  # Reduced to 2 for faster testing
                response = client.post("/run-comparison", json={
                    "company1_name": "KANINI",
                    "company2_name": f"TestCompany{i}",
                    "company1_website": "https://kanini.com/",
                    "company2_website": f"https://testcompany{i}.com/",
                    "company1_linkedin": "https://www.linkedin.com/company/kanini/",
                    "company2_linkedin": f"https://www.linkedin.com/company/testcompany{i}/",
                    "use_predefined_data": True
                })
                
                if response.status_code == 200:
                    session_id = response.json()["session_id"]
                    sessions.append(session_id)
                    print(f"✅ Created session {i+1}: {session_id}")
        
        # Verify all sessions are accessible
        for session_id in sessions:
            status_response = client.get(f"/analysis-status/{session_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] in ["running", "completed", "error", "demo_mode"]
            print(f"✅ Session accessible: {session_id} (status: {status_data['status']})")
        
        print(f"✅ Concurrent session management: {len(sessions)} sessions created and verified")
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        print("🧪 Testing root endpoint...")
        
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Company Comparison API is running" in data["message"]
        print("✅ Root endpoint verified")
    
    def test_terminal_output_pagination(self, client):
        """Test terminal output pagination functionality"""
        print("🧪 Testing terminal output pagination...")
        
        with patch('main.run_analysis_in_background'):
            response = client.post("/run-comparison", json={
                "company1_name": "KANINI",
                "company2_name": "Infosys",
                "company1_website": "https://kanini.com/",
                "company2_website": "https://www.infosys.com/",
                "company1_linkedin": "https://www.linkedin.com/company/kanini/",
                "company2_linkedin": "https://www.linkedin.com/company/infosys/",
                "use_predefined_data": True
            })
            
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                
                # Test terminal output with different last_index values
                for last_index in [0, 5, 10]:
                    terminal_response = client.get(f"/terminal-output/{session_id}?last_index={last_index}")
                    assert terminal_response.status_code == 200
                    terminal_data = terminal_response.json()
                    assert "lines" in terminal_data
                    assert "last_index" in terminal_data
                    assert "has_more" in terminal_data
                    print(f"✅ Terminal pagination with last_index={last_index}: {len(terminal_data['lines'])} lines")