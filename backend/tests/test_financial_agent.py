import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financial_agent import FinancialAnalysisAgent, KANINI_PRE_SCRAPED_FINANCIAL_DATA

class TestFinancialAgent:
    
    @pytest.fixture
    def financial_agent(self):
        """Create financial agent instance for testing"""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            return FinancialAnalysisAgent("test-api-key")
    
    @pytest.fixture
    def sample_state(self):
        """Complete sample state for financial testing"""
        return {
            "company1_name": "KANINI",
            "company2_name": "Infosys",
            "company1_financials": {},
            "company2_financials": {},
            "company1_ratios": {},
            "company2_ratios": {},
            "company1_financial_analysis": "",
            "company2_financial_analysis": "",
            "profitability_comparison": "",
            "liquidity_comparison": "",
            "solvency_comparison": "",
            "growth_potential_analysis": "",
            "investment_recommendation": "",
            "final_financial_report": "",
            "executive_summary": "",
            "use_predefined_data": False  # Added missing field
        }
    
    @pytest.fixture
    def mock_financial_data(self):
        """Mock financial data for testing"""
        return {
            "revenue": 50000000,
            "net_income": 5000000,
            "total_assets": 100000000,
            "total_equity": 60000000,
            "current_assets": 30000000,
            "current_liabilities": 20000000
        }
    
    @pytest.fixture
    def mock_ratio_data(self):
        """Mock ratio data for testing"""
        return {
            "net_margin": 10.0,
            "roe": 15.0,
            "roa": 5.0,
            "current_ratio": 1.5,
            "debt_to_equity": 0.67
        }

    def test_agent_initialization(self, financial_agent):
        """Test financial agent initialization"""
        assert financial_agent.model_name == 'gemini-2.0-flash'
        assert financial_agent.scraper is not None
    
    def test_collect_financial_data_with_predefined(self, financial_agent, sample_state):
        """Test financial data collection with predefined Kanini data"""
        sample_state["use_predefined_data"] = True
        sample_state["company1_name"] = "Kanini Software"
        
        with patch.object(financial_agent.scraper, 'analyze_company') as mock_analyze:
            mock_analyze.return_value = (
                {"revenue": 100000000, "net_income": 8000000},
                {"roa": 8.0, "roe": 12.0}
            )
            
            result_state = financial_agent.collect_financial_data(sample_state)
            
            # Should use predefined data for Kanini
            assert result_state["company1_financials"]["revenue"] == 32000000
            assert result_state["company1_ratios"]["roe"] == 4.44
            # Company 2 should use scraped data
            assert "company2_financials" in result_state
    
    def test_collect_financial_data_normal(self, financial_agent, sample_state):
        """Test normal financial data collection"""
        sample_state["use_predefined_data"] = False
        
        with patch.object(financial_agent.scraper, 'analyze_company') as mock_analyze:
            mock_analyze.return_value = (
                {"revenue": 50000000, "net_income": 5000000},
                {"roa": 10.0, "roe": 15.0}
            )
            
            result_state = financial_agent.collect_financial_data(sample_state)
            
            assert "company1_financials" in result_state
            assert "company1_ratios" in result_state
            assert result_state["company1_financials"]["revenue"] == 50000000
            assert mock_analyze.call_count == 2  # Called for both companies
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_analyze_company1_financials(self, mock_generate, financial_agent, sample_state, mock_financial_data, mock_ratio_data):
        """Test financial analysis generation for company 1"""
        mock_response = Mock()
        mock_response.text = "Comprehensive financial analysis for company 1"
        mock_generate.return_value = mock_response
        
        sample_state["company1_financials"] = mock_financial_data
        sample_state["company1_ratios"] = mock_ratio_data
        
        result_state = financial_agent.analyze_company1_financials(sample_state)
        
        assert result_state["company1_financial_analysis"] == "Comprehensive financial analysis for company 1"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_analyze_company2_financials(self, mock_generate, financial_agent, sample_state, mock_financial_data, mock_ratio_data):
        """Test financial analysis generation for company 2"""
        mock_response = Mock()
        mock_response.text = "Comprehensive financial analysis for company 2"
        mock_generate.return_value = mock_response
        
        sample_state["company2_financials"] = mock_financial_data
        sample_state["company2_ratios"] = mock_ratio_data
        
        result_state = financial_agent.analyze_company2_financials(sample_state)
        
        assert result_state["company2_financial_analysis"] == "Comprehensive financial analysis for company 2"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_compare_profitability(self, mock_generate, financial_agent, sample_state, mock_financial_data, mock_ratio_data):
        """Test profitability comparison"""
        mock_response = Mock()
        mock_response.text = "Profitability comparison analysis"
        mock_generate.return_value = mock_response
        
        sample_state["company1_financials"] = mock_financial_data
        sample_state["company2_financials"] = mock_financial_data
        sample_state["company1_ratios"] = mock_ratio_data
        sample_state["company2_ratios"] = mock_ratio_data
        
        result_state = financial_agent.compare_profitability(sample_state)
        
        assert result_state["profitability_comparison"] == "Profitability comparison analysis"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_compare_liquidity_solvency(self, mock_generate, financial_agent, sample_state, mock_financial_data, mock_ratio_data):
        """Test liquidity and solvency comparison"""
        mock_response = Mock()
        mock_response.text = "Liquidity and solvency analysis"
        mock_generate.return_value = mock_response
        
        sample_state["company1_financials"] = mock_financial_data
        sample_state["company2_financials"] = mock_financial_data
        sample_state["company1_ratios"] = mock_ratio_data
        sample_state["company2_ratios"] = mock_ratio_data
        
        result_state = financial_agent.compare_liquidity_solvency(sample_state)
        
        assert "liquidity_comparison" in result_state
        assert "solvency_comparison" in result_state
        assert mock_generate.call_count == 2  # Called twice in this method
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_analyze_growth_potential(self, mock_generate, financial_agent, sample_state):
        """Test growth potential analysis"""
        mock_response = Mock()
        mock_response.text = "Growth potential analysis"
        mock_generate.return_value = mock_response
        
        # Set up required previous analyses
        sample_state["company1_financial_analysis"] = "Company 1 analysis"
        sample_state["company2_financial_analysis"] = "Company 2 analysis"
        sample_state["profitability_comparison"] = "Profitability analysis"
        sample_state["liquidity_comparison"] = "Liquidity analysis"
        
        result_state = financial_agent.analyze_growth_potential(sample_state)
        
        assert result_state["growth_potential_analysis"] == "Growth potential analysis"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_generate_investment_recommendation(self, mock_generate, financial_agent, sample_state):
        """Test investment recommendation generation"""
        mock_response = Mock()
        mock_response.text = "Investment recommendations"
        mock_generate.return_value = mock_response
        
        # Set up required previous analyses
        sample_state["company1_financial_analysis"] = "Company 1 analysis"
        sample_state["company2_financial_analysis"] = "Company 2 analysis"
        sample_state["profitability_comparison"] = "Profitability analysis"
        sample_state["liquidity_comparison"] = "Liquidity analysis"
        sample_state["growth_potential_analysis"] = "Growth analysis"
        
        result_state = financial_agent.generate_investment_recommendation(sample_state)
        
        assert result_state["investment_recommendation"] == "Investment recommendations"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_generate_final_financial_report(self, mock_generate, financial_agent, sample_state):
        """Test final report generation"""
        mock_response = Mock()
        mock_response.text = "Final financial report content"
        mock_generate.return_value = mock_response
        
        # Set up sample analysis data
        sample_state["company1_financial_analysis"] = "Company 1 analysis"
        sample_state["company2_financial_analysis"] = "Company 2 analysis"
        sample_state["profitability_comparison"] = "Profitability analysis"
        sample_state["liquidity_comparison"] = "Liquidity analysis"
        sample_state["growth_potential_analysis"] = "Growth analysis"
        sample_state["investment_recommendation"] = "Investment recs"
        
        result_state = financial_agent.generate_final_financial_report(sample_state)
        
        assert result_state["final_financial_report"] == "Final financial report content"
        mock_generate.assert_called_once()
    
    @patch('financial_agent.genai.GenerativeModel.generate_content')
    def test_generate_executive_summary(self, mock_generate, financial_agent, sample_state):
        """Test executive summary generation"""
        mock_response = Mock()
        mock_response.text = "Executive summary content"
        mock_generate.return_value = mock_response
        
        sample_state["final_financial_report"] = "Full report content"
        
        result_state = financial_agent.generate_executive_summary(sample_state)
        
        assert result_state["executive_summary"] == "Executive summary content"
        mock_generate.assert_called_once()

    def test_scraper_methods_exist(self, financial_agent):
        """Test that the actual scraper methods exist"""
        assert hasattr(financial_agent.scraper, 'analyze_company')
    
    def test_predefined_data_available(self):
        """Test that predefined Kanini data is available"""
        assert "revenue" in KANINI_PRE_SCRAPED_FINANCIAL_DATA
        assert KANINI_PRE_SCRAPED_FINANCIAL_DATA["revenue"] == 32000000

    def test_error_handling(self, financial_agent, sample_state):
        """Test error handling in data collection"""
        with patch.object(financial_agent.scraper, 'analyze_company', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                financial_agent.collect_financial_data(sample_state)