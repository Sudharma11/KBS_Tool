import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linkedin_agent import LinkedInAnalysisAgent, KANINI_PRE_SCRAPED_LINKEDIN_DATA

class TestLinkedInAgent:
    
    @pytest.fixture
    def linkedin_agent(self):
        """Create LinkedIn agent instance for testing"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            return LinkedInAnalysisAgent("test-api-key")
    
    @pytest.fixture
    def sample_state(self):
        """Complete sample state for LinkedIn testing"""
        return {
            "company1_url": "https://linkedin.com/company/kanini",
            "company2_url": "https://linkedin.com/company/infosys", 
            "company1_name": "KANINI",
            "company1_linkedin_data": {},
            "company2_linkedin_data": {},
            "company1_structured": {},
            "company2_structured": {},
            "company1_business_analysis": "",
            "company2_business_analysis": "",
            "company1_tech_analysis": "",
            "company2_tech_analysis": "",
            "company1_talent_analysis": "",
            "company2_talent_analysis": "",
            "company1_engagement_analysis": "",
            "company2_engagement_analysis": "",
            "comparison_analysis": "",
            "final_report": "",
            "executive_briefing": "",
            "use_predefined_data": False  # Added missing field
        }
    
    @pytest.fixture
    def sample_linkedin_data(self):
        """Sample LinkedIn data structure"""
        return {
            "basic_info": {
                "company_name": "Test Company",
                "tagline": "Test tagline", 
                "followers": "10K"
            },
            "about_details": {
                "website": "https://test.com",
                "industry": "Information Technology",
                "headquarters": "Test City",
                "founded": "2020", 
                "company_size": "501-1000 employees",
                "specialties": "AI, Machine Learning, Cloud",
                "associated_members": "500"
            },
            "overview": {
                "summary": "Test company summary"
            },
            "people": {
                "linkedin_employees": "400"
            },
            "posts": [
                {
                    "content": "We're hiring software engineers! Python and AWS experience required.",
                    "engagement": {"reactions": "50", "comments": "10"}
                },
                {
                    "content": "New AI product launch with machine learning capabilities",
                    "engagement": {"reactions": "100", "comments": "25"}
                }
            ],
            "jobs": [
                {"title": "Software Engineer", "location": "Remote"},
                {"title": "Data Scientist", "location": "Bangalore"},
                {"title": "Cloud Architect", "location": "Hybrid"}
            ],
            "page_links": {
                "posts_page": "https://linkedin.com/company/test/posts",
                "people_page": "https://linkedin.com/company/test/people", 
                "jobs_page": "https://linkedin.com/company/test/jobs",
                "about_page": "https://linkedin.com/company/test/about"
            }
        }

    def test_agent_initialization(self, linkedin_agent):
        """Test LinkedIn agent initialization"""
        assert linkedin_agent.model_name == 'gemini-2.0-flash'
        assert linkedin_agent.scraper is not None

    @patch('linkedin_agent.SimpleLinkedInScraper.get_company_data')
    def test_collect_linkedin_data_normal(self, mock_scraper, linkedin_agent, sample_state):
        """Test LinkedIn data collection in normal mode"""
        mock_scraper.return_value = {"basic_info": {"company_name": "Infosys"}}
        
        sample_state["use_predefined_data"] = False
        result_state = linkedin_agent.collect_linkedin_data(sample_state)
        
        # Should scrape both companies
        assert "company1_linkedin_data" in result_state
        assert "company2_linkedin_data" in result_state
        assert mock_scraper.called

    @patch('linkedin_agent.SimpleLinkedInScraper.get_company_data') 
    def test_collect_linkedin_data_predefined(self, mock_scraper, linkedin_agent, sample_state):
        """Test LinkedIn data collection with predefined Kanini data"""
        mock_scraper.return_value = {"basic_info": {"company_name": "Infosys"}}
        
        sample_state["use_predefined_data"] = True
        result_state = linkedin_agent.collect_linkedin_data(sample_state)
        
        # Should use predefined for company1, scrape company2
        assert result_state["company1_linkedin_data"] == KANINI_PRE_SCRAPED_LINKEDIN_DATA
        assert "company2_linkedin_data" in result_state
        mock_scraper.assert_called_once()  # Only called for company2

    def test_structure_lscrape_data(self, linkedin_agent, sample_linkedin_data):
        """Test LinkedIn data structuring"""
        structured_data = linkedin_agent._structure_lscrape_data(
            sample_linkedin_data, 
            "https://linkedin.com/company/test"
        )
        
        expected_categories = [
            "company_identity", "business_profile", "talent_workforce",
            "content_engagement", "career_opportunities", "market_presence",
            "technical_indicators"
        ]
        
        assert all(category in structured_data for category in expected_categories)
        assert structured_data["company_identity"]["company_name"] == "Test Company"

    def test_extract_company_identity(self, linkedin_agent, sample_linkedin_data):
        """Test company identity extraction"""
        identity = linkedin_agent._extract_company_identity(sample_linkedin_data)
        
        assert identity["company_name"] == "Test Company"
        assert identity["industry"] == "Information Technology" 
        assert identity["company_size"] == "501-1000 employees"

    def test_extract_content_engagement(self, linkedin_agent, sample_linkedin_data):
        """Test content engagement analysis"""
        engagement = linkedin_agent._extract_content_engagement(sample_linkedin_data)
        
        assert engagement["post_frequency"] == 2
        assert engagement["total_posts_analyzed"] == 2
        assert "hiring" in engagement["content_themes"]
        assert engagement["average_engagement"] > 0

    def test_extract_career_opportunities(self, linkedin_agent, sample_linkedin_data):
        """Test career opportunities extraction"""
        careers = linkedin_agent._extract_career_opportunities(sample_linkedin_data)
        
        assert careers["active_job_openings"] == 3
        assert len(careers["technical_roles"]) == 3  # All roles are technical
        assert careers["hiring_intensity"] == "Medium"  # 3 jobs > threshold

    def test_is_technical_role(self, linkedin_agent):
        """Test technical role identification"""
        assert linkedin_agent._is_technical_role("Software Engineer") == True
        assert linkedin_agent._is_technical_role("Data Scientist") == True
        assert linkedin_agent._is_technical_role("Cloud Architect") == True
        assert linkedin_agent._is_technical_role("Marketing Manager") == False
        assert linkedin_agent._is_technical_role("HR Coordinator") == False

    def test_extract_technologies_from_text(self, linkedin_agent):
        """Test technology extraction from text"""
        text = "We use Python, React, AWS and machine learning for our projects"
        technologies = linkedin_agent._extract_technologies_from_text(text)
        
        assert "python" in technologies
        assert "aws" in technologies  
        assert "machine learning" in technologies

    def test_parse_engagement_number(self, linkedin_agent):
        """Test engagement number parsing"""
        assert linkedin_agent._parse_engagement_number("1.2K") == 1200
        assert linkedin_agent._parse_engagement_number("500") == 500
        assert linkedin_agent._parse_engagement_number("") == 0
        assert linkedin_agent._parse_engagement_number("1.5M") == 1500000

    @patch('linkedin_agent.genai.GenerativeModel.generate_content')
    def test_business_analysis_generation(self, mock_generate, linkedin_agent, sample_state):
        """Test business analysis generation"""
        mock_response = Mock()
        mock_response.text = "LinkedIn business analysis results"
        mock_generate.return_value = mock_response
        
        sample_state["company1_structured"] = {
            "company_identity": {"company_name": "Test Company"},
            "business_profile": {"company_summary": "Test summary"}
        }
        
        result_state = linkedin_agent.analyze_company1_business(sample_state)
        
        assert result_state["company1_business_analysis"] == "LinkedIn business analysis results"
        mock_generate.assert_called_once()

    @patch('linkedin_agent.genai.GenerativeModel.generate_content')
    def test_technology_analysis_generation(self, mock_generate, linkedin_agent, sample_state):
        """Test technology analysis generation"""
        mock_response = Mock()
        mock_response.text = "Technology analysis results"
        mock_generate.return_value = mock_response
        
        sample_state["company1_structured"] = {
            "technical_indicators": {"technologies_mentioned": ["python", "aws"]}
        }
        
        result_state = linkedin_agent.analyze_company1_technology(sample_state)
        
        assert result_state["company1_tech_analysis"] == "Technology analysis results"
        mock_generate.assert_called_once()

    @patch('linkedin_agent.genai.GenerativeModel.generate_content') 
    def test_talent_analysis_generation(self, mock_generate, linkedin_agent, sample_state):
        """Test talent analysis generation"""
        mock_response = Mock()
        mock_response.text = "Talent analysis results"
        mock_generate.return_value = mock_response
        
        sample_state["company1_structured"] = {
            "talent_workforce": {"linkedin_employees": "500"},
            "career_opportunities": {"active_job_openings": 5}
        }
        
        result_state = linkedin_agent.analyze_company1_talent(sample_state)
        
        assert result_state["company1_talent_analysis"] == "Talent analysis results"
        mock_generate.assert_called_once()

    @patch('linkedin_agent.genai.GenerativeModel.generate_content')
    def test_engagement_analysis_generation(self, mock_generate, linkedin_agent, sample_state):
        """Test engagement analysis generation"""
        mock_response = Mock()
        mock_response.text = "Engagement analysis results"
        mock_generate.return_value = mock_response
        
        sample_state["company1_structured"] = {
            "content_engagement": {"post_frequency": 10, "average_engagement": 25.5}
        }
        
        result_state = linkedin_agent.analyze_company1_engagement(sample_state)
        
        assert result_state["company1_engagement_analysis"] == "Engagement analysis results"
        mock_generate.assert_called_once()

    @patch('linkedin_agent.genai.GenerativeModel.generate_content')
    def test_company_comparison(self, mock_generate, linkedin_agent, sample_state):
        """Test company comparison analysis"""
        mock_response = Mock()
        mock_response.text = "Comparison analysis results"
        mock_generate.return_value = mock_response
        
        # Set up all required analysis data
        sample_state.update({
            "company1_business_analysis": "Business analysis 1",
            "company2_business_analysis": "Business analysis 2",
            "company1_tech_analysis": "Tech analysis 1", 
            "company2_tech_analysis": "Tech analysis 2",
            "company1_talent_analysis": "Talent analysis 1",
            "company2_talent_analysis": "Talent analysis 2", 
            "company1_engagement_analysis": "Engagement analysis 1",
            "company2_engagement_analysis": "Engagement analysis 2"
        })
        
        result_state = linkedin_agent.compare_companies(sample_state)
        
        assert result_state["comparison_analysis"] == "Comparison analysis results"
        mock_generate.assert_called_once()

    def test_default_structured_data(self, linkedin_agent):
        """Test default structured data generation"""
        default_data = linkedin_agent._get_default_structured_data("https://test.com")
        
        expected_structure = [
            "company_identity", "business_profile", "talent_workforce",
            "content_engagement", "career_opportunities", "market_presence", 
            "technical_indicators"
        ]
        
        assert all(key in default_data for key in expected_structure)
        assert default_data["company_identity"]["company_name"] == "Unknown"

    def test_predefined_data_available(self):
        """Test that predefined Kanini LinkedIn data is available"""
        assert "KANINI" in KANINI_PRE_SCRAPED_LINKEDIN_DATA["basic_info"]["company_name"]
        assert "posts" in KANINI_PRE_SCRAPED_LINKEDIN_DATA
        assert "jobs" in KANINI_PRE_SCRAPED_LINKEDIN_DATA

    @patch('linkedin_agent.genai.GenerativeModel.generate_content')
    def test_complete_workflow(self, mock_generate, linkedin_agent, sample_state):
        """Test complete LinkedIn agent workflow"""
        # Mock all AI calls (13 total in complete workflow)
        mock_responses = [Mock(text=f"Analysis {i}") for i in range(13)]
        mock_generate.side_effect = mock_responses

        # Execute main workflow steps
        state_after_collect = linkedin_agent.collect_linkedin_data(sample_state)
        state_after_extract = linkedin_agent.extract_structured_data(state_after_collect)
        state_after_business1 = linkedin_agent.analyze_company1_business(state_after_extract)
        state_after_business2 = linkedin_agent.analyze_company2_business(state_after_business1)
        state_after_tech1 = linkedin_agent.analyze_company1_technology(state_after_business2)
        state_after_tech2 = linkedin_agent.analyze_company2_technology(state_after_tech1)
        state_after_talent1 = linkedin_agent.analyze_company1_talent(state_after_tech2)
        state_after_talent2 = linkedin_agent.analyze_company2_talent(state_after_talent1)
        state_after_engagement1 = linkedin_agent.analyze_company1_engagement(state_after_talent2)
        state_after_engagement2 = linkedin_agent.analyze_company2_engagement(state_after_engagement1)
        state_after_compare = linkedin_agent.compare_companies(state_after_engagement2)
        
        # Verify all analysis fields are populated
        assert state_after_compare["company1_business_analysis"] != ""
        assert state_after_compare["company2_business_analysis"] != ""
        assert state_after_compare["company1_tech_analysis"] != ""
        assert state_after_compare["company2_tech_analysis"] != ""
        assert state_after_compare["company1_talent_analysis"] != ""
        assert state_after_compare["company2_talent_analysis"] != ""
        assert state_after_compare["company1_engagement_analysis"] != ""
        assert state_after_compare["company2_engagement_analysis"] != ""
        assert state_after_compare["comparison_analysis"] != ""