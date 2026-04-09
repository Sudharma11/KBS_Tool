import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from website_agent import LangGraphCompanyComparator, KANINI_PRE_SCRAPED_DATA

class TestWebsiteAgent:
    
    @pytest.fixture
    def website_agent(self):
        """Create website agent instance for testing"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            return LangGraphCompanyComparator("test-api-key")
    
    @pytest.fixture
    def sample_state(self):
        """Complete sample state for testing"""
        return {
            "company1_url": "https://kanini.com/",
            "company2_url": "https://infosys.com/",
            "company1_raw_data": "Sample website content for company 1",
            "company2_raw_data": "Sample website content for company 2",
            "company1_structured": {},
            "company2_structured": {},
            "company1_business_analysis": "",
            "company2_business_analysis": "",
            "company1_tech_analysis": "", 
            "company2_tech_analysis": "",
            "comparison_analysis": "",
            "final_report": "",
            "executive_briefing": "",
            "use_predefined_data": False  # Added missing field
        }
    
    def test_agent_initialization(self, website_agent):
        """Test website agent initialization"""
        assert website_agent.model_name == 'gemini-2.0-flash'
        assert website_agent.scraper is not None
    
    @patch('website_agent.WebsiteScraper.scrape_company_website')
    def test_scrape_data_normal_mode(self, mock_scrape, website_agent, sample_state):
        """Test website scraping in normal mode (no predefined data)"""
        mock_scrape.side_effect = [
            "Scraped data for company 1",
            "Scraped data for company 2"
        ]
        
        sample_state["use_predefined_data"] = False
        result_state = website_agent.scrape_data(sample_state)
        
        # Should scrape both companies
        assert mock_scrape.call_count == 2
        assert result_state["company1_raw_data"] == "Scraped data for company 1"
        assert result_state["company2_raw_data"] == "Scraped data for company 2"
    
    @patch('website_agent.WebsiteScraper.scrape_company_website')
    def test_scrape_data_with_predefined(self, mock_scrape, website_agent, sample_state):
        """Test website scraping with predefined Kanini data"""
        mock_scrape.return_value = "Scraped data for company 2"
        
        sample_state["use_predefined_data"] = True
        result_state = website_agent.scrape_data(sample_state)
        
        # Should use predefined for company1, scrape only company2
        assert mock_scrape.call_count == 1  # Only called for company2
        assert result_state["company1_raw_data"] == KANINI_PRE_SCRAPED_DATA
        assert result_state["company2_raw_data"] == "Scraped data for company 2"
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_extract_structured_data_success(self, mock_generate, website_agent, sample_state):
        """Test successful structured data extraction"""
        mock_response_1 = Mock()
        mock_response_1.text = json.dumps({
            "company_identity": {"company_name": "Company 1"},
            "business_offerings": {"core_services": ["Service A"]}
        })
        
        mock_response_2 = Mock()
        mock_response_2.text = json.dumps({
            "company_identity": {"company_name": "Company 2"},
            "business_offerings": {"core_services": ["Service B"]}
        })
        
        mock_generate.side_effect = [mock_response_1, mock_response_2]
        
        result_state = website_agent.extract_structured_data(sample_state)
        
        assert "company_identity" in result_state["company1_structured"]
        assert "company_identity" in result_state["company2_structured"]
        assert result_state["company1_structured"]["company_identity"]["company_name"] == "Company 1"
        assert result_state["company2_structured"]["company_identity"]["company_name"] == "Company 2"
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_extract_structured_data_fallback(self, mock_generate, website_agent, sample_state):
        """Test fallback to default data when extraction fails"""
        mock_generate.side_effect = Exception("API Error")
        
        result_state = website_agent.extract_structured_data(sample_state)
        
        # Should use default structured data for both companies
        assert result_state["company1_structured"]["company_identity"]["company_name"] == "Company 1"
        assert result_state["company2_structured"]["company_identity"]["company_name"] == "Company 2"
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_business_analysis(self, mock_generate, website_agent, sample_state):
        """Test business analysis generation for both companies"""
        mock_response = Mock()
        mock_response.text = "Comprehensive business analysis results"
        mock_generate.return_value = mock_response
        
        # Set up structured data
        sample_state["company1_structured"] = {
            "business_offerings": {"core_services": ["IT Consulting"]}
        }
        sample_state["company2_structured"] = {
            "business_offerings": {"core_services": ["Cloud Services"]}
        }
        
        # Test company 1 business analysis
        state_after_1 = website_agent.analyze_company1_business(sample_state)
        assert state_after_1["company1_business_analysis"] == "Comprehensive business analysis results"
        
        # Test company 2 business analysis  
        state_after_2 = website_agent.analyze_company2_business(state_after_1)
        assert state_after_2["company2_business_analysis"] == "Comprehensive business analysis results"
        
        assert mock_generate.call_count == 2
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_technology_analysis(self, mock_generate, website_agent, sample_state):
        """Test technology analysis generation for both companies"""
        mock_response = Mock()
        mock_response.text = "Comprehensive technology analysis results"
        mock_generate.return_value = mock_response
        
        # Set up structured data
        sample_state["company1_structured"] = {
            "technical_capabilities": {"technology_stack": ["Python", "AWS"]}
        }
        sample_state["company2_structured"] = {
            "technical_capabilities": {"technology_stack": ["Java", "Azure"]}
        }
        
        # Test company 1 technology analysis
        state_after_1 = website_agent.analyze_company1_technology(sample_state)
        assert state_after_1["company1_tech_analysis"] == "Comprehensive technology analysis results"
        
        # Test company 2 technology analysis
        state_after_2 = website_agent.analyze_company2_technology(state_after_1)
        assert state_after_2["company2_tech_analysis"] == "Comprehensive technology analysis results"
        
        assert mock_generate.call_count == 2
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_company_comparison(self, mock_generate, website_agent, sample_state):
        """Test company comparison analysis"""
        mock_response = Mock()
        mock_response.text = "Comprehensive comparison analysis"
        mock_generate.return_value = mock_response
        
        # Set up required analysis data
        sample_state["company1_business_analysis"] = "Business analysis 1"
        sample_state["company2_business_analysis"] = "Business analysis 2"
        sample_state["company1_tech_analysis"] = "Tech analysis 1"
        sample_state["company2_tech_analysis"] = "Tech analysis 2"
        sample_state["company1_structured"] = {"company_identity": {"name": "Company 1"}}
        sample_state["company2_structured"] = {"company_identity": {"name": "Company 2"}}
        
        result_state = website_agent.compare_companies(sample_state)
        
        assert result_state["comparison_analysis"] == "Comprehensive comparison analysis"
        mock_generate.assert_called_once()
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_report_generation(self, mock_generate, website_agent, sample_state):
        """Test final report and executive briefing generation"""
        mock_response = Mock()
        mock_response.text = "Generated report content"
        mock_generate.return_value = mock_response
        
        # Set up all required analysis data
        sample_state.update({
            "company1_business_analysis": "Business analysis 1",
            "company2_business_analysis": "Business analysis 2", 
            "company1_tech_analysis": "Tech analysis 1",
            "company2_tech_analysis": "Tech analysis 2",
            "comparison_analysis": "Comparison analysis",
            "company1_structured": {"company_identity": {"name": "Company 1"}},
            "company2_structured": {"company_identity": {"name": "Company 2"}}
        })
        
        # Test final report generation
        state_after_report = website_agent.generate_final_report(sample_state)
        assert state_after_report["final_report"] == "Generated report content"
        
        # Test executive briefing generation
        state_after_briefing = website_agent.generate_executive_briefing(state_after_report)
        assert state_after_briefing["executive_briefing"] == "Generated report content"
        
        assert mock_generate.call_count == 2
    
    def test_default_structured_data(self, website_agent):
        """Test default structured data generation"""
        default_data_1 = website_agent._get_default_structured_data(1)
        default_data_2 = website_agent._get_default_structured_data(2)
        
        expected_structure = {
            "company_identity", "business_offerings", "company_profile",
            "technical_capabilities", "market_presence", "business_model_analysis"
        }
        
        assert all(key in default_data_1 for key in expected_structure)
        assert all(key in default_data_2 for key in expected_structure)
        assert default_data_1["company_identity"]["company_name"] == "Company 1"
        assert default_data_2["company_identity"]["company_name"] == "Company 2"
    
    @patch('website_agent.genai.GenerativeModel.generate_content')
    def test_complete_workflow(self, mock_generate, website_agent, sample_state):
        """Test complete website agent workflow"""
        # Mock 9 AI calls for complete workflow
        mock_responses = [Mock(text=f"Analysis result {i}") for i in range(9)]
        mock_generate.side_effect = mock_responses

        # Execute complete workflow
        state_after_scrape = website_agent.scrape_data(sample_state)
        state_after_extract = website_agent.extract_structured_data(state_after_scrape)
        state_after_business1 = website_agent.analyze_company1_business(state_after_extract)
        state_after_business2 = website_agent.analyze_company2_business(state_after_business1)
        state_after_tech1 = website_agent.analyze_company1_technology(state_after_business2)
        state_after_tech2 = website_agent.analyze_company2_technology(state_after_tech1)
        state_after_compare = website_agent.compare_companies(state_after_tech2)
        state_after_report = website_agent.generate_final_report(state_after_compare)
        final_state = website_agent.generate_executive_briefing(state_after_report)
        
        # Verify all analysis fields are populated
        assert final_state["company1_business_analysis"] != ""
        assert final_state["company2_business_analysis"] != ""
        assert final_state["company1_tech_analysis"] != ""
        assert final_state["company2_tech_analysis"] != ""
        assert final_state["comparison_analysis"] != ""
        assert final_state["final_report"] != ""
        assert final_state["executive_briefing"] != ""
        
        # Verify correct number of AI calls
        assert mock_generate.call_count == 9
    
    def test_predefined_data_available(self):
        """Test that predefined Kanini data is available"""
        assert "KANINI" in KANINI_PRE_SCRAPED_DATA
        assert "https://kanini.com/" in KANINI_PRE_SCRAPED_DATA
        assert "Cloud Enablement" in KANINI_PRE_SCRAPED_DATA