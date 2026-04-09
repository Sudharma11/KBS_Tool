import pytest
import json
from unittest.mock import patch, Mock, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph_orches import run_unified_comparison, UnifiedCompanyComparator, create_professional_word_document

class TestAgentIntegration:
    
    @pytest.fixture
    def sample_companies_data(self):
        """Complete sample companies data for integration testing"""
        return {
            "company1_name": "KANINI",
            "company2_name": "Infosys", 
            "company1_website": "https://kanini.com/",
            "company2_website": "https://www.infosys.com/",
            "company1_linkedin": "https://www.linkedin.com/company/kanini/",
            "company2_linkedin": "https://www.linkedin.com/company/infosys/",
            "session_id": "test_session_123",
            "use_predefined_data": False
        }
    
    @pytest.fixture
    def sample_companies_data_no_optional(self):
        """Sample data without optional parameters"""
        return {
            "company1_name": "KANINI",
            "company2_name": "Infosys", 
            "company1_website": "https://kanini.com/",
            "company2_website": "https://www.infosys.com/",
            "company1_linkedin": "https://www.linkedin.com/company/kanini/",
            "company2_linkedin": "https://www.linkedin.com/company/infosys/"
        }
    
    @pytest.fixture
    def complete_initial_state(self, sample_companies_data):
        """Complete initial state matching orchestrator requirements"""
        return {
            **sample_companies_data,
            "website_final_report": "",
            "linkedin_final_report": "", 
            "financial_final_report": "",
            "final_unified_report": ""
        }

    def test_unified_comparison_success(self, sample_companies_data):
        """Test successful unified comparison with all agents"""
        # Mock the actual agent functions with correct names
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    # Mock agent responses with correct structure
                    mock_website.return_value = {
                        "final_report": "Website analysis final report content",
                        "executive_briefing": "Website executive summary"
                    }
                    
                    mock_linkedin.return_value = {
                        "final_report": "LinkedIn analysis final report content",
                        "executive_briefing": "LinkedIn executive summary" 
                    }
                    
                    mock_financial.return_value = {
                        "final_financial_report": "Financial analysis final report content",
                        "executive_summary": "Financial executive summary"
                    }
                    
                    # Mock Gemini for final report generation
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Unified comprehensive report content"
                        mock_gemini.return_value = mock_response
                        
                        # Mock Word document creation to avoid file I/O during tests
                        with patch('langgraph_orches.create_professional_word_document') as mock_word_doc:
                            mock_doc = Mock()
                            mock_word_doc.return_value = mock_doc
                            
                            result = run_unified_comparison(**sample_companies_data)
                    
                    # Verify all agents were called with correct parameters
                    mock_website.assert_called_once()
                    mock_linkedin.assert_called_once()
                    mock_financial.assert_called_once()
                    
                    # Verify result structure
                    assert "final_unified_report" in result
                    assert "website_final_report" in result
                    assert "linkedin_final_report" in result 
                    assert "financial_final_report" in result
                    assert result["company1_name"] == "KANINI"
                    assert result["company2_name"] == "Infosys"

    def test_unified_comparison_with_predefined_data(self, sample_companies_data_no_optional):
        """Test unified comparison with predefined data enabled"""
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    mock_website.return_value = {"final_report": "Website report"}
                    mock_linkedin.return_value = {"final_report": "LinkedIn report"}
                    mock_financial.return_value = {"final_financial_report": "Financial report"}
                    
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Unified report"
                        mock_gemini.return_value = mock_response
                        
                        with patch('langgraph_orches.create_professional_word_document'):
                            # Test with predefined data enabled - pass all parameters individually
                            result = run_unified_comparison(
                                company1_name=sample_companies_data_no_optional["company1_name"],
                                company2_name=sample_companies_data_no_optional["company2_name"],
                                company1_website=sample_companies_data_no_optional["company1_website"],
                                company2_website=sample_companies_data_no_optional["company2_website"],
                                company1_linkedin=sample_companies_data_no_optional["company1_linkedin"],
                                company2_linkedin=sample_companies_data_no_optional["company2_linkedin"],
                                use_predefined_data=True
                            )
                    
                    # Verify predefined data flag was passed
                    call_kwargs = mock_financial.call_args[1]
                    assert call_kwargs.get('use_predefined_data') == True

    def test_unified_comparison_partial_failure(self, sample_companies_data_no_optional):
        """Test unified comparison with partial agent failures"""
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    # Mock one agent to fail
                    mock_website.side_effect = Exception("Website analysis failed")
                    mock_linkedin.return_value = {"final_report": "LinkedIn report content"}
                    mock_financial.return_value = {"final_financial_report": "Financial report content"}
                    
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Partial unified report"
                        mock_gemini.return_value = mock_response
                        
                        with patch('langgraph_orches.create_professional_word_document'):
                            result = run_unified_comparison(**sample_companies_data_no_optional)
                    
                    # Should still complete with error messages in the report
                    assert "final_unified_report" in result
                    assert "website_final_report" in result
                    assert "Website analysis failed" in result["website_final_report"]

    def test_unified_comparator_initialization(self):
        """Test unified comparator initialization"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            comparator = UnifiedCompanyComparator("test-api-key")
            
            assert comparator.model_name == 'gemini-2.0-flash'
            assert comparator.model is not None

    def test_workflow_node_execution(self, complete_initial_state):
        """Test individual workflow node execution"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            comparator = UnifiedCompanyComparator("test-api-key")
            
            # Mock the agent calls
            with patch.object(comparator, 'run_website_analysis') as mock_website:
                with patch.object(comparator, 'run_linkedin_analysis') as mock_linkedin:
                    with patch.object(comparator, 'run_financial_analysis') as mock_financial:
                        with patch.object(comparator, 'generate_final_unified_report') as mock_report:
                            
                            # Setup return values that maintain state
                            def website_side_effect(state):
                                return {**state, "website_final_report": "Website report content"}
                            
                            def linkedin_side_effect(state):
                                return {**state, "linkedin_final_report": "LinkedIn report content"}
                            
                            def financial_side_effect(state):
                                return {**state, "financial_final_report": "Financial report content"}
                            
                            def report_side_effect(state):
                                return {**state, "final_unified_report": "Unified report content"}
                            
                            mock_website.side_effect = website_side_effect
                            mock_linkedin.side_effect = linkedin_side_effect
                            mock_financial.side_effect = financial_side_effect
                            mock_report.side_effect = report_side_effect
                            
                            # Test workflow sequence
                            state_after_website = comparator.run_website_analysis(complete_initial_state)
                            state_after_linkedin = comparator.run_linkedin_analysis(state_after_website)
                            state_after_financial = comparator.run_financial_analysis(state_after_linkedin)
                            final_state = comparator.generate_final_unified_report(state_after_financial)
                            
                            # Verify state progression
                            assert final_state["website_final_report"] == "Website report content"
                            assert final_state["linkedin_final_report"] == "LinkedIn report content"
                            assert final_state["financial_final_report"] == "Financial report content"
                            assert final_state["final_unified_report"] == "Unified report content"
                            assert final_state["company1_name"] == "KANINI"
                            assert final_state["company2_name"] == "Infosys"

    def test_word_document_creation(self):
        """Test Word document creation functionality"""
        test_content = """
        COMPREHENSIVE COMPANY COMPARISON REPORT
        ========================================
        
        EXECUTIVE SUMMARY
        =================
        Test executive summary content.
        
        1.0 INTRODUCTION
        ================
        Introduction content here.
        
        • Bullet point 1
        • Bullet point 2
        """
        
        # Mock the Document class to avoid file I/O
        with patch('langgraph_orches.Document') as mock_document_class:
            mock_doc = Mock()
            mock_document_class.return_value = mock_doc
            
            # Mock paragraph methods
            mock_paragraph = Mock()
            mock_doc.add_paragraph.return_value = mock_paragraph
            mock_doc.add_heading.return_value = Mock()
            mock_doc.add_page_break.return_value = None
            
            # Call the function
            doc = create_professional_word_document(
                test_content,
                "Test Report",
                "Company A", 
                "Company B",
                "test_session"
            )
            
            # Verify document was created
            assert doc is not None
            mock_document_class.assert_called_once()

    def test_workflow_with_session_id(self, sample_companies_data_no_optional):
        """Test workflow execution with session ID"""
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    mock_website.return_value = {"final_report": "Website report"}
                    mock_linkedin.return_value = {"final_report": "LinkedIn report"}
                    mock_financial.return_value = {"final_financial_report": "Financial report"}
                    
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Unified report"
                        mock_gemini.return_value = mock_response
                        
                        with patch('langgraph_orches.create_professional_word_document'):
                            # Test with session ID - pass all parameters individually
                            result = run_unified_comparison(
                                company1_name=sample_companies_data_no_optional["company1_name"],
                                company2_name=sample_companies_data_no_optional["company2_name"],
                                company1_website=sample_companies_data_no_optional["company1_website"],
                                company2_website=sample_companies_data_no_optional["company2_website"],
                                company1_linkedin=sample_companies_data_no_optional["company1_linkedin"],
                                company2_linkedin=sample_companies_data_no_optional["company2_linkedin"],
                                session_id="custom_session_123"
                            )
                    
                    assert result["session_id"] == "custom_session_123"

    def test_all_agents_failure(self, sample_companies_data_no_optional):
        """Test workflow when all agents fail"""
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    # All agents fail
                    mock_website.side_effect = Exception("Website failed")
                    mock_linkedin.side_effect = Exception("LinkedIn failed")
                    mock_financial.side_effect = Exception("Financial failed")
                    
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Unified report with errors"
                        mock_gemini.return_value = mock_response
                        
                        with patch('langgraph_orches.create_professional_word_document'):
                            result = run_unified_comparison(**sample_companies_data_no_optional)
                    
                    # Should still return a result with error messages
                    assert "final_unified_report" in result
                    assert "failed" in result["website_final_report"]
                    assert "failed" in result["linkedin_final_report"]
                    assert "failed" in result["financial_final_report"]

    def test_unified_comparison_without_optional_params(self, sample_companies_data_no_optional):
        """Test unified comparison without optional parameters"""
        with patch('langgraph_orches.run_website_comparison') as mock_website:
            with patch('langgraph_orches.run_linkedin_comparison') as mock_linkedin:
                with patch('langgraph_orches.run_financial_comparison') as mock_financial:
                    
                    mock_website.return_value = {"final_report": "Website report"}
                    mock_linkedin.return_value = {"final_report": "LinkedIn report"}
                    mock_financial.return_value = {"final_financial_report": "Financial report"}
                    
                    with patch('langgraph_orches.genai.GenerativeModel.generate_content') as mock_gemini:
                        mock_response = Mock()
                        mock_response.text = "Unified report"
                        mock_gemini.return_value = mock_response
                        
                        with patch('langgraph_orches.create_professional_word_document'):
                            # Test without optional parameters (should use defaults)
                            result = run_unified_comparison(**sample_companies_data_no_optional)
                    
                    # Should still work with default values
                    assert "final_unified_report" in result
                    assert result["session_id"] is None  # Should be None by default