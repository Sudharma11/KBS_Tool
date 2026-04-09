import os
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from app.scrapers.website_scraper import WebsiteScraper
from app.core.llm_client import LLMClient
from app.core.config import LLM_API_KEY, LLM_MODEL
from dotenv import load_dotenv

load_dotenv()

# Predefined Kanini data
KANINI_PRE_SCRAPED_DATA = """
COMPANY BASIC INFORMATION
============================================================
Company Name: Trailblazers of Digital Transformation
Website: https://kanini.com/
Title: Trailblazers of Digital Transformation | KANINI
Description: KANINI is a trusted digital transformation enabler, creating impeccable customer experiences through thoughtfully designed digital & data solutions and automated workflows.

============================================================
CONTACT INFORMATION
============================================================
Contact Page: https://kanini.com/contact-us/
Emails: transformations@kanini.com
Phones: +91 02069116911, 207 101 0766, 4469044000, 4224639800, 0206911691

============================================================
PRODUCTS & SERVICES
============================================================
1. SecOps
2. Cloud Enablement
3. Know More
4. Manufacturing
5. Generative AI
6. data with AI, ML, and Data Engineering
7. ServiceNow

============================================================
ABOUT THE COMPANY
============================================================
ABOUT PAGES:
- About Us: https://kanini.com/about-us/

COMPANY DESCRIPTION:
1. What We Do Product Engineering End-to-end Software Development Cloud Enablement App Modernization Cloud Enablement UI/UX DevOps Quality Engineering Product Engineeringfor Healthcare Product Engineering for Healthcare Product Engineering for BFSI Product Engineeringfor BFSI Data Analytics & AI Data E...
2. Product Engineering End-to-end Software Development Cloud Enablement App Modernization Cloud Enablement UI/UX DevOps Quality Engineering Product Engineeringfor Healthcare Product Engineering for Healthcare Product Engineering for BFSI Product Engineeringfor BFSI Data Analytics & AI Data Engineering ...

============================================================
IMPORTANT PAGES
============================================================
- Product Engineering: https://kanini.com/product-engineering/
- Product Engineeringfor Healthcare: https://kanini.com/
- Generative AI: https://kanini.com/generative-ai-solutions/
- ServiceNow: https://kanini.com/servicenow/
- Advisory and Consulting: https://kanini.com/servicenow-advisory-and-consulting/
- CMDB: https://kanini.com/servicenow-configuration-management-database-cmdb/
- GRC: https://kanini.com/servicenow/grc-governance-risk-compliance/
- SecOps: https://kanini.com/servicenow/security-operations-secops/

============================================================
SOCIAL MEDIA LINKS
============================================================
Linkedin: https://www.linkedin.com/company/kanini
Twitter: https://twitter.com/kanini_com
Youtube: https://www.youtube.com/channel/uc61gud71xnbkc2rfa_suyvq

============================================================
DETECTED TECHNOLOGIES
============================================================
WordPress, jQuery, Google Analytics, WordPress 6.8.3
"""

class ComparisonState(TypedDict):
    company1_url: str
    company2_url: str
    company1_raw_data: str
    company2_raw_data: str
    company1_structured: Dict[str, Any]
    company2_structured: Dict[str, Any]
    company1_business_analysis: str
    company2_business_analysis: str
    company1_tech_analysis: str
    company2_tech_analysis: str
    comparison_analysis: str
    final_report: str
    company2_individual_report: str
    executive_briefing: str
    use_predefined_data: bool
    company2_sources: List[str]

class LangGraphCompanyComparator:
    def __init__(self, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
        self.llm = LLMClient(api_key=api_key, model=model or None)
        print(f"LangGraphCompanyComparator using model: {self.llm.model}")
        self.scraper = WebsiteScraper()

    def _call_model(self, prompt: str) -> str:
        return self.llm.generate(prompt)
    
    def scrape_data(self, state: ComparisonState) -> ComparisonState:
        """Scrape both company websites or use predefined data for Kanini"""
        print("Collecting company website data...")
        
        # Check if we should use predefined data for company1 (Kanini)
        use_predefined = state.get("use_predefined_data", False)
        
        if use_predefined:
            print("Using predefined Kanini website data")
            state["company1_raw_data"] = KANINI_PRE_SCRAPED_DATA
            print("Predefined Kanini website data loaded successfully")
        else:
            state["company1_raw_data"] = self.scraper.scrape_company_website(state["company1_url"])
        
        # Always scrape company2 normally
        state["company2_raw_data"] = self.scraper.scrape_company_website(state["company2_url"])

        # Collect company2 source URLs from scraped text
        base = state["company2_url"].rstrip('/')
        sources = [base]
        for line in state["company2_raw_data"].split('\n'):
            line = line.strip()
            if line.startswith('http') and line not in sources:
                sources.append(line)
            elif ': http' in line:
                url = line.split(': ', 1)[-1].strip()
                if url.startswith('http') and url not in sources:
                    sources.append(url)
        state["company2_sources"] = sources[:10]

        print("Website data collection completed!")
        return state
    
    def extract_structured_data(self, state: ComparisonState) -> ComparisonState:
        """Enhanced structured data extraction using multi-agent approach"""
        print("Extracting structured company data...")
        
        # Extract for company 1
        extraction_prompt_1 = f"""
        As a Company Data Extractor, analyze and structure this scraped company data:
        
        {state["company1_raw_data"]}
        
        Extract the following comprehensive information as JSON:
        {{
            "company_identity": {{
                "company_name": "extracted name",
                "website_title": "page title",
                "meta_description": "meta description",
                "logo_url": "logo URL if available"
            }},
            "business_offerings": {{
                "core_services": ["list of main services"],
                "service_categories": ["categorized services"],
                "key_capabilities": ["business capabilities"],
                "pricing_mentions": ["any pricing information"]
            }},
            "company_profile": {{
                "mission_statement": "mission if available",
                "vision_statement": "vision if available", 
                "company_description": "about company text",
                "core_values": ["values if mentioned"],
                "history_timeline": "historical information"
            }},
            "technical_capabilities": {{
                "technology_stack": ["technologies used"],
                "digital_infrastructure": "infrastructure details",
                "stack_maturity": "high/medium/low",
                "innovation_indicators": ["innovative technologies"]
            }},
            "market_presence": {{
                "social_media_footprint": {{"platform": "url"}},
                "key_website_pages": ["important pages"],
                "contact_structure": "contact information quality",
                "geographic_reach": "global/regional/local"
            }},
            "business_model_analysis": {{
                "primary_model": "B2B/B2C/B2B2C",
                "revenue_streams": ["potential revenue sources"],
                "target_customer_segments": ["target markets"],
                "value_proposition": "core value offered"
            }}
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            extracted_data_1 = self._call_model(extraction_prompt_1)
            if extracted_data_1.startswith('```json'):
                extracted_data_1 = extracted_data_1[7:]
            if extracted_data_1.endswith('```'):
                extracted_data_1 = extracted_data_1[:-3]
            state["company1_structured"] = json.loads(extracted_data_1)
            print("Successfully extracted structured data for Company 1")
        except Exception as e:
            print(f"Could not extract structured data for company 1: {e}")
            state["company1_structured"] = self._get_default_structured_data(1)
        
        # Extract for company 2
        extraction_prompt_2 = f"""
        As a Company Data Extractor, analyze and structure this scraped company data:
        
        {state["company2_raw_data"]}
        
        Extract the following comprehensive information as JSON:
        {{
            "company_identity": {{
                "company_name": "extracted name",
                "website_title": "page title",
                "meta_description": "meta description",
                "logo_url": "logo URL if available"
            }},
            "business_offerings": {{
                "core_services": ["list of main services"],
                "service_categories": ["categorized services"],
                "key_capabilities": ["business capabilities"],
                "pricing_mentions": ["any pricing information"]
            }},
            "company_profile": {{
                "mission_statement": "mission if available",
                "vision_statement": "vision if available", 
                "company_description": "about company text",
                "core_values": ["values if mentioned"],
                "history_timeline": "historical information"
            }},
            "technical_capabilities": {{
                "technology_stack": ["technologies used"],
                "digital_infrastructure": "infrastructure details",
                "stack_maturity": "high/medium/low",
                "innovation_indicators": ["innovative technologies"]
            }},
            "market_presence": {{
                "social_media_footprint": {{"platform": "url"}},
                "key_website_pages": ["important pages"],
                "contact_structure": "contact information quality",
                "geographic_reach": "global/regional/local"
            }},
            "business_model_analysis": {{
                "primary_model": "B2B/B2C/B2B2C",
                "revenue_streams": ["potential revenue sources"],
                "target_customer_segments": ["target markets"],
                "value_proposition": "core value offered"
            }}
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            extracted_data_2 = self._call_model(extraction_prompt_2)
            if extracted_data_2.startswith('```json'):
                extracted_data_2 = extracted_data_2[7:]
            if extracted_data_2.endswith('```'):
                extracted_data_2 = extracted_data_2[:-3]
            state["company2_structured"] = json.loads(extracted_data_2)
            print("Successfully extracted structured data for Company 2")
        except Exception as e:
            print(f"Could not extract structured data for company 2: {e}")
            state["company2_structured"] = self._get_default_structured_data(2)
        
        print("Data extraction completed!")
        return state
    
    def _get_default_structured_data(self, company_number):
        """Provide default structured data when extraction fails"""
        return {
            "company_identity": {
                "company_name": f"Company {company_number}",
                "website_title": "Unknown",
                "meta_description": "Unknown",
                "logo_url": ""
            },
            "business_offerings": {
                "core_services": [],
                "service_categories": [],
                "key_capabilities": [],
                "pricing_mentions": []
            },
            "company_profile": {
                "mission_statement": "Unknown",
                "vision_statement": "Unknown",
                "company_description": "Unknown",
                "core_values": [],
                "history_timeline": "Unknown"
            },
            "technical_capabilities": {
                "technology_stack": [],
                "digital_infrastructure": "Unknown",
                "stack_maturity": "Unknown",
                "innovation_indicators": []
            },
            "market_presence": {
                "social_media_footprint": {},
                "key_website_pages": [],
                "contact_structure": "Unknown",
                "geographic_reach": "Unknown"
            },
            "business_model_analysis": {
                "primary_model": "Unknown",
                "revenue_streams": [],
                "target_customer_segments": [],
                "value_proposition": "Unknown"
            }
        }
    
    def analyze_company1_business(self, state: ComparisonState) -> ComparisonState:
        """Business Strategy Analyst role analysis for company 1"""
        print("Performing business strategy analysis for Company 1...")
        business_prompt = f"""
        As a Business Strategy Analyst, analyze this company's business strategy:
        
        {json.dumps(state["company1_structured"], indent=2)}
        
        Provide a comprehensive business analysis covering:
        
        1. BUSINESS MODEL ASSESSMENT:
           - Core business model identification
           - Revenue stream analysis
           - Scalability potential
           - Market diversification
        
        2. TARGET MARKET ANALYSIS:
           - Primary customer segments
           - Market positioning
           - Competitive landscape position
           - Growth opportunities
        
        3. VALUE PROPOSITION ANALYSIS:
           - Unique value proposition
           - Competitive advantages
           - Service differentiation
           - Market gap identification
        
        4. STRATEGIC POSITIONING:
           - Industry positioning
           - Brand strength indicators
           - Market leadership potential
           - Strategic vulnerabilities
        
        Provide detailed, data-driven insights in a structured format.
        """
        
        state["company1_business_analysis"] = self._call_model(business_prompt)
        return state
    
    def analyze_company2_business(self, state: ComparisonState) -> ComparisonState:
        """Business Strategy Analyst role analysis for company 2"""
        print("Performing business strategy analysis for Company 2...")
        business_prompt = f"""
        As a Business Strategy Analyst, analyze this company's business strategy:
        
        {json.dumps(state["company2_structured"], indent=2)}
        
        Provide a comprehensive business analysis covering:
        
        1. BUSINESS MODEL ASSESSMENT:
           - Core business model identification
           - Revenue stream analysis
           - Scalability potential
           - Market diversification
        
        2. TARGET MARKET ANALYSIS:
           - Primary customer segments
           - Market positioning
           - Competitive landscape position
           - Growth opportunities
        
        3. VALUE PROPOSITION ANALYSIS:
           - Unique value proposition
           - Competitive advantages
           - Service differentiation
           - Market gap identification
        
        4. STRATEGIC POSITIONING:
           - Industry positioning
           - Brand strength indicators
           - Market leadership potential
           - Strategic vulnerabilities
        
        Provide detailed, data-driven insights in a structured format.
        """
        
        state["company2_business_analysis"] = self._call_model(business_prompt)
        return state
    
    def analyze_company1_technology(self, state: ComparisonState) -> ComparisonState:
        """Technology Stack Analyst role analysis for company 1"""
        print("Performing technology stack analysis for Company 1...")
        tech_prompt = f"""
        As a Technology Stack Analyst, analyze this company's technical capabilities:
        
        {json.dumps(state["company1_structured"], indent=2)}
        
        Provide a comprehensive technology analysis covering:
        
        1. TECHNOLOGY STACK ASSESSMENT:
           - Stack modernity and relevance
           - Technical sophistication level
           - Infrastructure robustness
           - Innovation indicators
        
        2. DIGITAL CAPABILITIES:
           - Website technical quality
           - Digital marketing capabilities
           - Online presence strength
           - Technical scalability
        
        3. COMPETITIVE TECHNICAL ADVANTAGES:
           - Technical differentiators
           - Innovation capabilities
           - Technical debt indicators
           - Future-readiness
        
        4. TECHNOLOGY MATURITY:
           - Digital transformation stage
           - Technical team capabilities (inferred)
           - DevOps maturity
           - Security considerations
        
        Provide detailed technical insights in a structured format.
        """
        
        state["company1_tech_analysis"] = self._call_model(tech_prompt)
        return state
    
    def analyze_company2_technology(self, state: ComparisonState) -> ComparisonState:
        """Technology Stack Analyst role analysis for company 2"""
        print("Performing technology stack analysis for Company 2...")
        tech_prompt = f"""
        As a Technology Stack Analyst, analyze this company's technical capabilities:
        
        {json.dumps(state["company2_structured"], indent=2)}
        
        Provide a comprehensive technology analysis covering:
        
        1. TECHNOLOGY STACK ASSESSMENT:
           - Stack modernity and relevance
           - Technical sophistication level
           - Infrastructure robustness
           - Innovation indicators
        
        2. DIGITAL CAPABILITIES:
           - Website technical quality
           - Digital marketing capabilities
           - Online presence strength
           - Technical scalability
        
        3. COMPETITIVE TECHNICAL ADVANTAGES:
           - Technical differentiators
           - Innovation capabilities
           - Technical debt indicators
           - Future-readiness
        
        4. TECHNOLOGY MATURITY:
           - Digital transformation stage
           - Technical team capabilities (inferred)
           - DevOps maturity
           - Security considerations
        
        Provide detailed technical insights in a structured format.
        """
        
        state["company2_tech_analysis"] = self._call_model(tech_prompt)
        return state
    def generate_company2_individual_report(self, state: ComparisonState) -> ComparisonState:
        """Generate individual report for Company 2 only"""
        sources = state.get("company2_sources", [state.get("company2_url", "")])
        sources_text = "\n".join(f"- {s}" for s in sources)

        report_prompt = f"""
        As a Professional Report Generator, create an individual WEBSITE INTELLIGENCE report for Company 2 only:

        COMPANY 2 ANALYSIS:
        Structured Data: {json.dumps(state["company2_structured"], indent=2)}
        Business Analysis: {state["company2_business_analysis"]}
        Technology Analysis: {state["company2_tech_analysis"]}

        VERIFIED SOURCE URLs (use ONLY these for href links):
        {sources_text}

        Generate a professional individual WEBSITE INTELLIGENCE report with this structure:

        ================================================================================
                                WEBSITE ANALYSIS REPORT
                                        
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [Brief overview of key website findings]

        COMPANY PROFILE
        ===============
        1.0 Business Identity & Positioning
        1.1 Core Services & Offerings
        1.2 Target Market Analysis
        1.3 Value Proposition

        2.0 TECHNICAL CAPABILITIES
        ==========================
        2.1 Technology Stack Assessment
        2.2 Digital Infrastructure
        2.3 Technical Maturity
        2.4 Innovation Indicators

        3.0 DIGITAL PRESENCE
        ====================
        3.1 Website Quality Assessment
        3.2 Content Strategy
        3.3 User Experience
        3.4 Online Branding

        4.0 COMPETITIVE POSITIONING
        ===========================
        4.1 Market Position
        4.2 Competitive Advantages
        4.3 Growth Opportunities

        5.0 STRATEGIC RECOMMENDATIONS
        =============================
        5.1 Immediate Improvements
        5.2 Strategic Initiatives
        5.3 Long-term Development

        CONCLUSION
        ==========
        [Summary of key findings and final assessment]

        
        **URL INTEGRATION RULES:**
        1. Use EXACTLY 2 href links in the entire report - no more, no less
        2. Place links only in sections where they provide direct evidence for major findings
        3. Choose the 2 most significant findings that have clear URL evidence
        4. Format: <a href="FULL_URL" target="_blank">Descriptive Link Text</a>
        5. Links must be placed within the text, not as separate items
        6. Example: If service offerings are a major strength, link to services page
        7. Example: If technical capabilities are exceptional, link to relevant technology page
        
        **EXAMPLE URL USAGE (choose only 2 most significant):**
        - For exceptional service offerings: link to the company services page
        - For strong technical capabilities: link to the company technology page
        - For impressive case studies: link to the company case studies page

        Focus on creating a comprehensive individual assessment of Company 2's website presence with clear data source attribution.
        """

        state["company2_individual_report"] = self._call_model(report_prompt)
        return state

    def compare_companies(self, state: ComparisonState) -> ComparisonState:
        """Company Comparison Specialist role analysis"""
        print("Conducting comprehensive comparison...")
        comparison_prompt = f"""
        As a Company Comparison Specialist, conduct a comprehensive analysis:
        
        COMPANY 1 STRUCTURED DATA:
        {json.dumps(state["company1_structured"], indent=2)}
        
        COMPANY 1 BUSINESS ANALYSIS:
        {state["company1_business_analysis"]}
        
        COMPANY 1 TECHNOLOGY ANALYSIS:
        {state["company1_tech_analysis"]}
        
        COMPANY 2 STRUCTURED DATA:
        {json.dumps(state["company2_structured"], indent=2)}
        
        COMPANY 2 BUSINESS ANALYSIS:
        {state["company2_business_analysis"]}
        
        COMPANY 2 TECHNOLOGY ANALYSIS:
        {state["company2_tech_analysis"]}
        
        Provide a detailed comparative analysis covering:
        
        BUSINESS COMPARISON:
        • Service offerings overlap and differentiation
        • Business model compatibility/competition
        • Target market similarities and differences
        • Value proposition comparison
        • Competitive advantage analysis
        
        TECHNOLOGY COMPARISON:
        • Technology stack sophistication comparison
        • Digital capabilities assessment
        • Innovation and R&D indicators
        • Technical competitive positioning
        
        STRATEGIC ASSESSMENT:
        • Market positioning relative to each other
        • Partnership potential
        • Competitive threats
        • Strategic opportunities
        
        Provide actionable insights and strategic recommendations.
        """
        
        state["comparison_analysis"] = self._call_model(comparison_prompt)
        print("Website comparison completed!")
        return state
    
    def generate_final_report(self, state: ComparisonState) -> ComparisonState:
        """Professional Report Generator role - creates final comprehensive report with proper formatting"""
        from datetime import datetime
        
        report_prompt = f"""
        As a Professional Report Generator, create a comprehensive WEBSITE INTELLIGENCE report:

        COMPANY 1 ANALYSIS:
        Structured Data: {json.dumps(state["company1_structured"], indent=2)}
        Business Analysis: {state["company1_business_analysis"]}
        Technology Analysis: {state["company1_tech_analysis"]}
        
        COMPANY 2 ANALYSIS:
        Structured Data: {json.dumps(state["company2_structured"], indent=2)}
        Business Analysis: {state["company2_business_analysis"]}
        Technology Analysis: {state["company2_tech_analysis"]}
        
        COMPARISON ANALYSIS:
        {state["comparison_analysis"]}

        Generate a professional WEBSITE INTELLIGENCE report with this structure:

        ================================================================================
                                    WEBSITE INTELLIGENCE ANALYSIS REPORT
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [Brief overview of key website findings and competitive positioning]

        TABLE OF CONTENTS
        =================
        1.0 Introduction & Methodology
        2.0 Company Website Profiles
        3.0 Technical Capabilities Comparison
        4.0 Business Strategy Analysis
        5.0 Digital Marketing Assessment
        6.0 Competitive Positioning
        7.0 Strategic Recommendations

        1.0 INTRODUCTION & METHODOLOGY
        ==============================
        1.1 Analysis Scope
        1.2 Data Collection Methods
        1.3 Assessment Framework

        2.0 COMPANY WEBSITE PROFILES
        ============================
        2.1 {state.get('company1_name', 'Company 1')} Website Analysis
            • Technical Stack & Infrastructure
            • Content Strategy & Messaging
            • User Experience Assessment
            • Conversion Optimization

        2.2 {state.get('company2_name', 'Company 2')} Website Analysis
            • Technical Stack & Infrastructure
            • Content Strategy & Messaging
            • User Experience Assessment
            • Conversion Optimization

        3.0 TECHNICAL CAPABILITIES COMPARISON
        =====================================
        3.1 Technology Stack Assessment

        4.0 BUSINESS STRATEGY ANALYSIS
        ==============================
        4.1 Value Proposition Comparison
        4.2 Service Offerings Analysis
        4.3 Target Market Alignment
        4.4 Competitive Differentiation

        5.0 DIGITAL MARKETING ASSESSMENT
        ================================
        5.1 Content Marketing Strategy
        5.2 Lead Generation Capabilities
        5.3 Brand Consistency

        6.0 COMPETITIVE POSITIONING
        ===========================
        6.1 Market Position Analysis
        6.2 Digital Maturity Comparison
        6.3 Innovation Indicators
        6.4 Growth Potential

        7.0 STRATEGIC RECOMMENDATIONS
        =============================
        7.1 Immediate Action Items
        7.2 Medium-term Initiatives
        7.3 Long-term Strategic Moves
        7.4 Key Performance Indicators

        CONCLUSION
        ==========
        [Summary of key findings and final assessment]

        DATA ACCURACY & JUSTIFICATION REQUIREMENTS:
        1. For every analysis point, explicitly state the data source from the scraped information
        2. Include justification phrases like "Based on website content analysis..." or "Supported by service offerings found on..."
        3. When making comparative statements, specify the exact website elements that support the conclusion
        4. Use qualifying language such as "as evidenced by..." or "this conclusion is drawn from..."
        5. For technical assessments, reference specific detected technologies or infrastructure mentions
        6. In strategic recommendations, connect each suggestion to specific findings from the website analysis
        
        EXAMPLE FORMAT:
        - "Company A demonstrates stronger digital presence, as evidenced by their comprehensive service pages and detailed case studies found at [specific URL]"
        - "The technical assessment indicates modern infrastructure, justified by the detection of cloud technologies and responsive design implementation"
        - "This recommendation is supported by the gap analysis between Company A's detailed pricing page and Company B's limited pricing transparency"

        Ensure every analytical conclusion includes its data justification within the same sentence or immediately following it.
        Maintain professional business formatting while embedding accuracy qualifiers throughout the report.

        Ensure the report follows professional business formatting with clear sections, subsections, and actionable insights.
        """
        
        state["final_report"] = self._call_model(report_prompt)
        return state
    
    def generate_executive_briefing(self, state: ComparisonState) -> ComparisonState:
        """Generate a condensed executive summary"""
        briefing_prompt = f"""
        Create a one-page executive briefing from this comprehensive report:
        
        {state["final_report"]}
        
        Extract and condense into:
        
        🚀 EXECUTIVE BRIEFING
        =====================
        
        • KEY FINDINGS (3-5 bullet points)
        • STRATEGIC IMPLICATIONS
        • CRITICAL RECOMMENDATIONS
        • RISK ASSESSMENT SUMMARY
        • OPPORTUNITY MATRIX
        • DECISION POINTS
        
        Keep it under 400 words, focused on actionable insights for C-level executives.
        """
        
        state["executive_briefing"] = self._call_model(briefing_prompt)
        return state

def create_comparison_workflow(api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Create the LangGraph workflow"""
    workflow = StateGraph(ComparisonState)
    
    comparator = LangGraphCompanyComparator(api_key=api_key, model=model)
    
    # Add nodes
    workflow.add_node("scrape_data", comparator.scrape_data)
    workflow.add_node("extract_structured_data", comparator.extract_structured_data)
    workflow.add_node("analyze_company1_business", comparator.analyze_company1_business)
    workflow.add_node("analyze_company2_business", comparator.analyze_company2_business)
    workflow.add_node("analyze_company1_technology", comparator.analyze_company1_technology)
    workflow.add_node("analyze_company2_technology", comparator.analyze_company2_technology)
    workflow.add_node("compare_companies", comparator.compare_companies)
    workflow.add_node("generate_final_report", comparator.generate_final_report)
    workflow.add_node("generate_executive_briefing", comparator.generate_executive_briefing)
    workflow.add_node("generate_company2_individual_report", comparator.generate_company2_individual_report) 
    
    # Define workflow
    workflow.set_entry_point("scrape_data")
    workflow.add_edge("scrape_data", "extract_structured_data")
    workflow.add_edge("extract_structured_data", "analyze_company1_business")
    workflow.add_edge("analyze_company1_business", "analyze_company2_business")
    workflow.add_edge("analyze_company2_business", "analyze_company1_technology")
    workflow.add_edge("analyze_company1_technology", "analyze_company2_technology")
    workflow.add_edge("analyze_company2_technology", "compare_companies")
    workflow.add_edge("compare_companies", "generate_final_report")
    workflow.add_edge("generate_final_report", "generate_executive_briefing")
    workflow.add_edge("generate_executive_briefing", "generate_company2_individual_report")
    workflow.add_edge("generate_company2_individual_report", END)
    
    return workflow.compile()

# Updated usage example with predefined data option
def run_website_comparison(company1_url, company2_url, use_predefined_data=False, company1_name="KANINI", api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    workflow = create_comparison_workflow(api_key=api_key, model=model)
    
    initial_state = {
        "company1_url": company1_url,
        "company2_url": company2_url,
        "company1_name": company1_name,  # Add company name for identification
        "company1_raw_data": "",
        "company2_raw_data": "",
        "company1_structured": {},
        "company2_structured": {},
        "company1_business_analysis": "",
        "company2_business_analysis": "",
        "company1_tech_analysis": "",
        "company2_tech_analysis": "",
        "comparison_analysis": "",
        "final_report": "",
        "company2_individual_report": "",
        "executive_briefing": "",
        "use_predefined_data": use_predefined_data,
        "company2_sources": [],
    }
    
    result = workflow.invoke(initial_state)
    
    return result

def main():
    import time
    import json
    
    if not LLM_API_KEY:
        print("ERROR: Please set LLM_API_KEY in your .env file.")
        return
    
    try:
        # Get user input
        print("ENHANCED MULTI-AGENT COMPANY COMPARISON WITH LANGGRAPH")
        print("=" * 60)
        print("This system uses specialized AI agents for comprehensive")
        print("business intelligence and strategic analysis.")
        print("=" * 60)
        
        company1_url = input("\nEnter the first company website URL: ").strip()
        company2_url = input("Enter the second company website URL: ").strip()
        
        # Ask about predefined data
        use_predefined = input("Use predefined Kanini data? (y/n): ").strip().lower() == 'y'
        
        # Validate and format URLs
        if not company1_url.startswith(('http://', 'https://')):
            company1_url = 'https://' + company1_url
        if not company2_url.startswith(('http://', 'https://')):
            company2_url = 'https://' + company2_url
        
        print(f"\nCOMPARISON REQUEST:")
        print(f"   Company 1: {company1_url}")
        print(f"   Company 2: {company2_url}")
        print(f"   Predefined data: {'Yes' if use_predefined else 'No'}")
        print("\nThis may take 3-5 minutes...")
        print("   (Multi-agent analysis with comprehensive business intelligence)\n")
        
        # Perform enhanced comparison
        start_time = time.time()
        result = run_website_comparison(company1_url, company2_url, use_predefined_data=use_predefined)
        end_time = time.time()
        
        print(f"Analysis completed in {end_time - start_time:.1f} seconds")
        
        # Show executive briefing preview
        print("\nEXECUTIVE BRIEFING PREVIEW:")
        print("=" * 60)
        lines = result["executive_briefing"].split('\n')
        for line in lines:
            print(line)
        print("=" * 60)
        print("Full strategic analysis saved in the complete report.")
        
        print(f"\nCOMPREHENSIVE ANALYSIS COMPLETED!")
        print(f"Full report: company_comparison_langgraph_full.txt")
        print(f"Executive briefing: company_comparison_langgraph_executive.txt")
        print(f"Analysis depth: Multi-agent comprehensive analysis with LangGraph")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your API key is valid")
        print("2. Verify the website URLs are accessible")
        print("3. Ensure you have internet connectivity")
        print("4. Try using 'gemini-pro' if 'gemini-2.0-flash' is unavailable")

if __name__ == "__main__":
    main()
