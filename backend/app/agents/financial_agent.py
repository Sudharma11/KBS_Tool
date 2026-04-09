import os
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from app.scrapers.financial_scraper import WorkingFinancialScraper
from app.core.llm_client import LLMClient
from app.core.config import LLM_API_KEY, LLM_MODEL
from dotenv import load_dotenv

load_dotenv()

KANINI_PRE_SCRAPED_FINANCIAL_DATA = {
    "revenue": 32000000,  
    "operating_income": 2400000, 
    "net_income": 1280000,  
    "total_equity": 28800000,  
    "total_assets": 48000000,  
    "current_assets": 19200000,  
    "current_liabilities": 14400000,  
    "total_debt": 19200000,  
    "gross_profit": 19200000, 
    "estimated": True,
    "confidence": "high",
    "data_source": "Predefined Kanini Financial Data"
}

KANINI_PRE_SCRAPED_RATIOS = {
    "operating_margin": 7.50,
    "net_margin": 4.00,
    "roa": 2.67,
    "roe": 4.44,
    "gross_margin": 60.00,
    "current_ratio": 1.33,
    "debt_to_equity": 0.67,
    "debt_to_assets": 0.40
}

class FinancialComparisonState(TypedDict):
    company1_name: str
    company2_name: str
    company1_financials: Dict[str, Any]
    company2_financials: Dict[str, Any]
    company1_ratios: Dict[str, Any]
    company2_ratios: Dict[str, Any]
    company1_financial_analysis: str
    company2_financial_analysis: str
    profitability_comparison: str
    liquidity_comparison: str
    solvency_comparison: str
    growth_potential_analysis: str
    investment_recommendation: str
    final_financial_report: str
    company2_individual_report: str
    executive_summary: str
    use_predefined_data: bool
    company2_sources: List[str]

class FinancialAnalysisAgent:

    def __init__(self, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
        self.llm = LLMClient(api_key=api_key, model=model or None)
        print(f"FinancialAnalysisAgent using model: {self.llm.model}")
        self.scraper = WorkingFinancialScraper()
    
    
    def collect_financial_data(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Collect financial data for both companies"""
        print("Collecting financial data for both companies...")
        
        # Check if we should use predefined data for company1 (Kanini)
        use_predefined = state.get("use_predefined_data", False)
        company1_name = state.get("company1_name", "").lower()
        
        if use_predefined and "kanini" in company1_name:
            print("Using predefined Kanini financial data")
            state["company1_financials"] = KANINI_PRE_SCRAPED_FINANCIAL_DATA
            state["company1_ratios"] = KANINI_PRE_SCRAPED_RATIOS
            print("Predefined Kanini financial data loaded successfully")
        else:
            # Get financial data for company 1 normally
            company1_financials, company1_ratios = self.scraper.analyze_company(state['company1_name'])
            state["company1_financials"] = company1_financials
            state["company1_ratios"] = company1_ratios
        
        # Always analyze company 2 normally
        company2_financials, company2_ratios = self.scraper.analyze_company(state['company2_name'])
        state["company2_financials"] = company2_financials
        state["company2_ratios"] = company2_ratios

        # Collect company2 financial source URLs
        company2_name_slug = state['company2_name'].lower().replace(' ', '')
        sources = []
        data_source = company2_financials.get('data_source', '')
        if 'yahoo' in data_source.lower():
            symbol = company2_financials.get('symbol', '')
            if symbol:
                sources.append(f"https://finance.yahoo.com/quote/{symbol}")
        sources.append(f"https://www.{company2_name_slug}.com")
        sources.append(f"https://www.{company2_name_slug}.com/investors")
        state["company2_sources"] = [s for s in sources if s]

        print("Financial data collection completed!")
        return state
    
    def analyze_company1_financials(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Financial Analyst role - comprehensive analysis for company 1"""
        print("Performing detailed financial analysis for Company 1...")
        
        analysis_prompt = f"""
        As a Senior Financial Analyst, conduct a comprehensive financial analysis for:
        
        COMPANY: {state['company1_name']}
        
        FINANCIAL DATA:
        {json.dumps(state['company1_financials'], indent=2)}
        
        FINANCIAL RATIOS:
        {json.dumps(state['company1_ratios'], indent=2)}
        
        Provide a detailed financial analysis covering:
        
        1. PROFITABILITY ASSESSMENT:
           - Revenue quality and sustainability
           - Profit margin analysis (gross, operating, net)
           - Return metrics (ROA, ROE)
           - Cost structure efficiency
        
        2. LIQUIDITY POSITION:
           - Current ratio analysis
           - Working capital adequacy
           - Cash flow generation capability
           - Short-term financial health
        
        3. SOLVENCY & FINANCIAL STABILITY:
           - Debt-to-equity analysis
           - Asset coverage ratios
           - Long-term financial stability
           - Financial leverage assessment
        
        4. GROWTH POTENTIAL:
           - Revenue growth indicators
           - Profit growth trajectory
           - Asset growth patterns
           - Market positioning for growth
        
        5. RISK ASSESSMENT:
           - Financial risk factors
           - Market risk exposure
           - Operational risk indicators
           - Overall financial health score (1-10)
        
        6. VALUATION ASSESSMENT:
           - Market cap analysis (if available)
           - Asset valuation
           - Earnings quality
           - Investment attractiveness
        
        Provide specific, data-driven insights with clear financial metrics.
        """
        
        state["company1_financial_analysis"] = self.llm.generate(analysis_prompt)
        return state
    
    def analyze_company2_financials(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Financial Analyst role - comprehensive analysis for company 2"""
        print("Performing detailed financial analysis for Company 2...")
        
        analysis_prompt = f"""
        As a Senior Financial Analyst, conduct a comprehensive financial analysis for:
        
        COMPANY: {state['company2_name']}
        
        FINANCIAL DATA:
        {json.dumps(state['company2_financials'], indent=2)}
        
        FINANCIAL RATIOS:
        {json.dumps(state['company2_ratios'], indent=2)}
        
        Provide a detailed financial analysis covering:
        
        1. PROFITABILITY ASSESSMENT:
           - Revenue quality and sustainability
           - Profit margin analysis (gross, operating, net)
           - Return metrics (ROA, ROE)
           - Cost structure efficiency
        
        2. LIQUIDITY POSITION:
           - Current ratio analysis
           - Working capital adequacy
           - Cash flow generation capability
           - Short-term financial health
        
        3. SOLVENCY & FINANCIAL STABILITY:
           - Debt-to-equity analysis
           - Asset coverage ratios
           - Long-term financial stability
           - Financial leverage assessment
        
        4. GROWTH POTENTIAL:
           - Revenue growth indicators
           - Profit growth trajectory
           - Asset growth patterns
           - Market positioning for growth
        
        5. RISK ASSESSMENT:
           - Financial risk factors
           - Market risk exposure
           - Operational risk indicators
           - Overall financial health score (1-10)
        
        6. VALUATION ASSESSMENT:
           - Market cap analysis (if available)
           - Asset valuation
           - Earnings quality
           - Investment attractiveness
        
        Provide specific, data-driven insights with clear financial metrics.
        """
        
        state["company2_financial_analysis"] = self.llm.generate(analysis_prompt)
        return state
    def generate_company2_individual_report(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Generate individual financial report for Company 2 only"""
        company2_name = state['company2_name']
        sources = state.get("company2_sources", [])
        sources_text = "\n".join(f"- {s}" for s in sources)

        report_prompt = f"""
        As a Financial Report Generator, create an individual qualitative financial report for Company 2 only:

        COMPANY: {state['company2_name']}
        
        FINANCIAL ANALYSIS:
        {state['company2_financial_analysis']}
        
        FINANCIAL DATA:
        {json.dumps(state['company2_financials'], indent=2)}
        
        FINANCIAL RATIOS:
        {json.dumps(state['company2_ratios'], indent=2)}

        VERIFIED SOURCE URLs (use ONLY these for href links):
        {sources_text}

        Generate a professional qualitative financial report with this structure:

        ================================================================================
                                FINANCIAL ANALYSIS REPORT
                                        
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [High-level qualitative financial assessment]

        FINANCIAL HEALTH ASSESSMENT
        ===========================
        1.0 BUSINESS EFFICIENCY PROFILE
            • Revenue Model Characteristics
            • Cost Management Approach
            • Profit Sustainability

        2.0 OPERATIONAL STABILITY
            • Business Resilience Factors
            • Resource Management Effectiveness
            • Financial Flexibility

        3.0 GROWTH TRAJECTORY
            • Expansion Potential
            • Market Position Advancement
            • Strategic Growth Capabilities

        4.0 COMPETITIVE FINANCIAL POSITIONING
            • Financial Stability Comparison
            • Risk Management Capabilities
            • Strategic Financial Advantages

        5.0 STRATEGIC FINANCIAL RECOMMENDATIONS
            • Financial Management Priorities
            • Investment Considerations
            • Risk Mitigation Strategies

        CONCLUSION
        ==========
        [Summary of financial positioning and strategic implications]

        DATA ACCURACY & SOURCE REFERENCES:
        1. For each financial assessment, specify the basis: "Based on comprehensive financial ratio analysis of {company2_name}..." 
        2. Include justification phrases: "This efficiency assessment is justified by the operational margin patterns observed in financial data..."
        3. When making qualitative statements, reference the analytical foundation: "as evidenced by the relative positioning in financial health indicators"
        4. Use qualifying language: "The stability analysis suggests..." or "Risk assessment indicates based on financial structure..."
        5. For strategic recommendations, connect to specific financial observations: "This priority is based on the identified patterns in financial performance metrics"

        
        IMPORTANT INSTRUCTIONS:
        - DO NOT include any specific financial numbers, metrics, or ratios
        - Focus on qualitative assessments and descriptive positioning
        - Use descriptive terms like "strong", "efficient", "well-positioned"
        - Maintain professional business language throughout
        - Embed accuracy justifications within the analysis sentences

        Provide clear, consistent qualitative insights without financial metrics but with embedded data justifications.
        """

        state["company2_individual_report"] = self.llm.generate(report_prompt)
        return state
    

    def compare_profitability(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Structured Qualitative Profitability Comparison"""
        print("Comparing business efficiency characteristics...")
        
        comparison_prompt = f"""
        Provide a structured qualitative comparison using this exact format:

        BUSINESS EFFICIENCY COMPARISON: {state['company1_name']} vs {state['company2_name']}

        REVENUE APPROACH CHARACTERISTICS:
        • Model Type: [Describe each company's revenue model style]
        • Income Stability: [Compare revenue predictability]
        • Growth Orientation: [Describe growth approach differences]

        COST MANAGEMENT PROFILE:
        • Efficiency Focus: [Compare operational efficiency emphasis]
        • Resource Allocation: [Describe resource utilization approaches]
        • Scalability Approach: [Compare scaling methodology]

        PROFIT SUSTAINABILITY:
        • Business Model Resilience: [Compare model durability]
        • Market Adaptation: [Describe change response capabilities]
        • Competitive Efficiency: [Compare market efficiency positioning]

        Use only qualitative descriptors. No numbers or metrics.
        Each section must contain exactly 3 bullet points.
        """
        
        state["profitability_comparison"] = self.llm.generate(comparison_prompt)
        return state

    def compare_liquidity_solvency(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Structured Business Stability Comparison"""
        print("Comparing operational stability...")
        
        comparison_prompt = f"""
        Provide a structured stability comparison using this exact format:

        OPERATIONAL STABILITY COMPARISON: {state['company1_name']} vs {state['company2_name']}

        BUSINESS RESILIENCE:
        • Operational Continuity: [Compare business continuity factors]
        • Risk Preparedness: [Describe risk management approaches]
        • Adaptability: [Compare change management capabilities]

        RESOURCE MANAGEMENT:
        • Asset Utilization: [Compare resource deployment effectiveness]
        • Liability Approach: [Describe obligation management styles]
        • Strategic Flexibility: [Compare operational maneuverability]

        SUSTAINABILITY POSITIONING:
        • Long-term Viability: [Compare business sustainability]
        • Market Position Stability: [Describe competitive standing durability]
        • Growth Foundation: [Compare expansion capability foundations]

        Use only qualitative descriptors. No numbers or metrics.
        Each section must contain exactly 3 bullet points.
        """
        
        result = self.llm.generate(comparison_prompt)
        state["liquidity_comparison"] = result
        state["solvency_comparison"] = result
        return state
    
    def analyze_growth_potential(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Growth Potential and Investment Analysis"""
        print("Analyzing growth potential and investment attractiveness...")
        
        analysis_prompt = f"""
        As a Growth Strategy and Investment Analyst, conduct growth potential analysis:
        
        COMPANY 1: {state['company1_name']}
        Financial Analysis: {state['company1_financial_analysis']}
        Financial Data: {json.dumps(state['company1_financials'], indent=2)}
        
        COMPANY 2: {state['company2_name']}
        Financial Analysis: {state['company2_financial_analysis']}
        Financial Data: {json.dumps(state['company2_financials'], indent=2)}
        
        Profitability Comparison: {state['profitability_comparison']}
        Liquidity/Solvency Comparison: {state['liquidity_comparison']}
        
        Provide comprehensive growth and investment analysis:
        
        GROWTH TRAJECTORY ASSESSMENT:
        • Revenue growth potential
        • Profit expansion capabilities
        • Asset growth sustainability
        • Market share expansion possibilities
        
        INVESTMENT ATTRACTIVENESS:
        • Valuation metrics comparison
        • Earnings quality assessment
        • Dividend potential (if applicable)
        • Total return expectations
        
        COMPETITIVE ADVANTAGE ANALYSIS:
        • Financial competitive advantages
        • Scale advantages
        • Efficiency advantages
        • Innovation investment capacity
        
        STRATEGIC GROWTH RECOMMENDATIONS:
        • Organic growth opportunities
        • Strategic investment areas
        • Risk-adjusted return potential
        • Growth sustainability assessment
        
        Provide clear growth scores and investment recommendations.
        """
        
        state["growth_potential_analysis"] = self.llm.generate(analysis_prompt)
        return state
    
    def generate_investment_recommendation(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Investment Recommendation Specialist"""
        print("Generating investment recommendations...")
        
        recommendation_prompt = f"""
        As a Chief Investment Officer, provide final investment recommendations:
        
        COMPANY 1: {state['company1_name']}
        Full Analysis: {state['company1_financial_analysis']}
        
        COMPANY 2: {state['company2_name']}
        Full Analysis: {state['company2_financial_analysis']}
        
        Profitability Comparison: {state['profitability_comparison']}
        Liquidity/Solvency: {state['liquidity_comparison']}
        Growth Potential: {state['growth_potential_analysis']}
        
        Provide clear, actionable investment recommendations:
        
        INVESTMENT DECISION MATRIX:
        • Preferred investment choice with rationale
        • Risk-adjusted return comparison
        • Investment horizon recommendations
        • Position sizing suggestions
        
        RISK ASSESSMENT:
        • Key investment risks for each company
        • Risk mitigation strategies
        • Worst-case scenario analysis
        • Exit strategy considerations
        
        PORTFOLIO STRATEGY:
        • Strategic allocation recommendations
        • Diversification benefits
        • Correlation analysis (if data allows)
        • Portfolio optimization suggestions
        
        PERFORMANCE EXPECTATIONS:
        • Short-term performance outlook (1 year)
        • Medium-term growth expectations (3 years)
        • Long-term value creation potential (5+ years)
        • Key performance indicators to monitor
        
        Provide a clear BUY/HOLD/SELL recommendation for each company.
        """
        
        state["investment_recommendation"] = self.llm.generate(recommendation_prompt)
        print("Financial comparison completed!")
        return state
    
    

    def generate_final_financial_report(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Comprehensive Financial Report Generator without financial metrics"""
        
        report_prompt = f"""
        As a Financial Report Generator, create a qualitative comparison report WITHOUT specific financial metrics:

        COMPANIES ANALYZED:
        • Company 1: {state['company1_name']}
        • Company 2: {state['company2_name']}

        ANALYSIS RESULTS:
        
        COMPANY 1 FINANCIAL ANALYSIS:
        {state['company1_financial_analysis']}
        
        COMPANY 2 FINANCIAL ANALYSIS:
        {state['company2_financial_analysis']}
        
        PROFITABILITY COMPARISON:
        {state['profitability_comparison']}
        
        LIQUIDITY & SOLVENCY COMPARISON:
        {state['liquidity_comparison']}
        
        GROWTH POTENTIAL ANALYSIS:
        {state['growth_potential_analysis']}
        
        INVESTMENT RECOMMENDATIONS:
        {state['investment_recommendation']}

        Generate a professional qualitative financial comparison report with this structure:

        ================================================================================
                            QUALITATIVE FINANCIAL COMPARISON REPORT
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [High-level qualitative comparison and strategic positioning]

        COMPARATIVE ANALYSIS
        ====================
        
        1.0 BUSINESS MODEL COMPARISON
        =============================
        1.1 Revenue Model Characteristics
        1.2 Cost Structure Efficiency
        1.3 Business Model Sustainability

        2.0 FINANCIAL HEALTH ASSESSMENT
        ===============================
        2.1 Overall Financial Stability
        2.2 Risk Management Capabilities
        2.3 Financial Resilience

        3.0 GROWTH TRAJECTORY COMPARISON
        ================================
        3.1 Expansion Potential
        3.2 Market Position Advancement
        3.3 Strategic Growth Initiatives

        4.0 COMPETITIVE POSITIONING
        ===========================
        4.1 Market Standing
        4.2 Competitive Advantages
        4.3 Industry Positioning

        5.0 STRATEGIC RECOMMENDATIONS
        =============================
        5.1 Strategic Priorities
        5.2 Risk Considerations
        5.3 Opportunity Areas

        DATA ACCURACY & JUSTIFICATION REQUIREMENTS:
        1. For each financial assessment, specify the basis: "Based on financial ratio analysis..." or "Supported by revenue model examination..."
        2. Include justification phrases: "This efficiency assessment is justified by the operational margin comparisons..." or "The growth potential conclusion is supported by historical performance patterns..."
        3. When making qualitative statements, reference the analytical foundation: "as evidenced by the relative positioning in industry benchmarks" or "this assessment draws from comparative financial health indicators"
        4. Use qualifying language: "The stability analysis suggests..." or "Risk assessment indicates..."
        5. For strategic recommendations, connect to specific financial observations: "This priority is based on the identified gap in operational efficiency between the companies"

        JUSTIFICATION INTEGRATION EXAMPLES:
        - "Company A demonstrates stronger financial resilience, as evidenced by their consistent performance patterns and balanced risk profile in the financial data analysis"
        - "The growth trajectory assessment indicates superior expansion potential, justified by the comparative analysis of market positioning and strategic initiatives"
        - "This strategic recommendation is supported by the identified opportunity in operational efficiency improvements based on the cost structure comparison"

        IMPORTANT INSTRUCTIONS:
        - DO NOT include any specific financial numbers, metrics, or ratios
        - Focus on qualitative comparisons and relative positioning
        - Use descriptive terms like "stronger", "weaker", "more efficient", "better positioned"
        - Maintain consistent reporting structure across analyses
        - Use comparative language without numerical benchmarks
        - Ensure professional business language throughout
        - Embed accuracy justifications within the analysis sentences themselves

        Provide clear, consistent qualitative insights without financial metrics but with embedded data justifications.
        """

        state["final_financial_report"] = self.llm.generate(report_prompt)
        return state
    
    def generate_executive_summary(self, state: FinancialComparisonState) -> FinancialComparisonState:
        """Generate condensed executive summary"""
        
        summary_prompt = f"""
        Create a one-page executive summary from this comprehensive financial report:
        
        {state["final_financial_report"]}
        
        Extract and condense into:
        
        🚀 FINANCIAL EXECUTIVE SUMMARY
        ==============================
        
        • KEY FINANCIAL FINDINGS (3-5 bullet points)
        • INVESTMENT RECOMMENDATION SUMMARY
        • RISK ASSESSMENT HIGHLIGHTS
        • GROWTH POTENTIAL COMPARISON
        • CRITICAL FINANCIAL METRICS
        • DECISION POINTS FOR INVESTORS
        
        Keep it under 400 words, focused on actionable financial insights for executives and investors.
        Include specific financial metrics and clear comparative rankings.
        """
        
        state["executive_summary"] = self.llm.generate(summary_prompt)
        return state

def create_financial_comparison_workflow(api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Create the LangGraph workflow for financial comparison"""
    workflow = StateGraph(FinancialComparisonState)
    
    financial_agent = FinancialAnalysisAgent(api_key=api_key, model=model)
    
    # Add nodes
    workflow.add_node("collect_financial_data", financial_agent.collect_financial_data)
    workflow.add_node("analyze_company1_financials", financial_agent.analyze_company1_financials)
    workflow.add_node("analyze_company2_financials", financial_agent.analyze_company2_financials)
    workflow.add_node("compare_profitability", financial_agent.compare_profitability)
    workflow.add_node("compare_liquidity_solvency", financial_agent.compare_liquidity_solvency)
    workflow.add_node("analyze_growth_potential", financial_agent.analyze_growth_potential)
    workflow.add_node("generate_investment_recommendation", financial_agent.generate_investment_recommendation)
    workflow.add_node("generate_final_financial_report", financial_agent.generate_final_financial_report)
    workflow.add_node("generate_executive_summary", financial_agent.generate_executive_summary)
    workflow.add_node("generate_company2_individual_report", financial_agent.generate_company2_individual_report)

    # Define workflow
    workflow.set_entry_point("collect_financial_data")
    workflow.add_edge("collect_financial_data", "analyze_company1_financials")
    workflow.add_edge("analyze_company1_financials", "analyze_company2_financials")
    workflow.add_edge("analyze_company2_financials", "compare_profitability")
    workflow.add_edge("compare_profitability", "compare_liquidity_solvency")
    workflow.add_edge("compare_liquidity_solvency", "analyze_growth_potential")
    workflow.add_edge("analyze_growth_potential", "generate_investment_recommendation")
    workflow.add_edge("generate_investment_recommendation", "generate_final_financial_report")
    workflow.add_edge("generate_final_financial_report", "generate_executive_summary")
    workflow.add_edge("generate_executive_summary", "generate_company2_individual_report")
    workflow.add_edge("generate_company2_individual_report", END) 
    
    return workflow.compile()


def run_financial_comparison(company1_name, company2_name, use_predefined_data=False, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Run the financial comparison workflow"""
    workflow = create_financial_comparison_workflow(api_key=api_key, model=model)
    
    initial_state = {
        "company1_name": company1_name,
        "company2_name": company2_name,
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
        "company2_individual_report": "",
        "executive_summary": "",
        "use_predefined_data": use_predefined_data,
        "company2_sources": [],
    }
    
    result = workflow.invoke(initial_state)
    
    return result

def main():
    import time
    
    if not LLM_API_KEY:
        print("ERROR: Please set LLM_API_KEY in your .env file.")
        return
    
    try:
        # Get user input
        print("ADVANCED FINANCIAL COMPARISON AI AGENT")
        print("=" * 60)
        print("This system uses specialized financial AI agents for")
        print("comprehensive financial analysis and investment recommendations.")
        print("=" * 60)
        
        company1_name = input("\nEnter the first company name: ").strip()
        company2_name = input("Enter the second company name: ").strip()
        
        
        use_predefined = input("Use predefined Kanini data? (y/n): ").strip().lower() == 'y'
        
        if not company1_name or not company2_name:
            print("Please provide both company names.")
            return
        
        print(f"\nFINANCIAL COMPARISON REQUEST:")
        print(f"   Company 1: {company1_name}")
        print(f"   Company 2: {company2_name}")
        print(f"   Predefined data: {'Yes' if use_predefined else 'No'}")
        print("\nThis may take 2-4 minutes...")
        print("   (Multi-agent financial analysis with comprehensive metrics)\n")
        
        # Perform financial comparison
        start_time = time.time()
        result = run_financial_comparison(company1_name, company2_name, use_predefined_data=use_predefined)
        end_time = time.time()
        
        print(f"Financial analysis completed in {end_time - start_time:.1f} seconds")
        
        # Show executive summary preview
        print("\nEXECUTIVE SUMMARY PREVIEW:")
        print("=" * 60)
        lines = result["executive_summary"].split('\n')
        for line in lines:
            print(line)
        print("=" * 60)
        
        # Display key financial metrics
        print(f"\nKEY FINANCIAL METRICS:")
        print(f"   {company1_name}:")
        if 'revenue' in result['company1_financials']:
            revenue = result['company1_financials']['revenue']
            print(f"     Revenue: ₹{revenue:,.0f}")
        if 'net_income' in result['company1_financials']:
            net_income = result['company1_financials']['net_income']
            print(f"     Net Income: ₹{net_income:,.0f}")
        
        print(f"   {company2_name}:")
        if 'revenue' in result['company2_financials']:
            revenue = result['company2_financials']['revenue']
            print(f"     Revenue: ₹{revenue:,.0f}")
        if 'net_income' in result['company2_financials']:
            net_income = result['company2_financials']['net_income']
            print(f"     Net Income: ₹{net_income:,.0f}")
        
        print(f"\nCOMPREHENSIVE FINANCIAL ANALYSIS COMPLETED!")
        print(f"Full report: financial_comparison_full_report.txt")
        print(f"Executive summary: financial_comparison_executive_summary.txt")
        print(f"Analysis depth: Multi-agent financial analysis with specialized roles")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your API key is valid")
        print("2. Verify the company names are correct")
        print("3. Ensure you have internet connectivity")
        print("4. Try using 'gemini-pro' if 'gemini-2.0-flash' is unavailable")

if __name__ == "__main__":
    main()
