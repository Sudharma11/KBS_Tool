import os
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from app.agents.website_agent import run_website_comparison
from app.agents.linkedin_agent import run_linkedin_comparison
from app.agents.financial_agent import run_financial_comparison
from app.core.llm_client import LLMClient
from app.core.config import LLM_API_KEY, LLM_MODEL
from dotenv import load_dotenv
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from datetime import datetime
import re
import docx.oxml.shared
import docx.opc.constants

# Load environment variables from .env file
load_dotenv()

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

class UnifiedComparisonState(TypedDict):
    # Input data
    company1_name: str
    company2_name: str
    company1_website: str
    company2_website: str
    company1_linkedin: str
    company2_linkedin: str
    session_id: str
    use_predefined_data: bool
    
    # Final reports from individual agents
    website_final_report: str
    linkedin_final_report: str
    financial_final_report: str
    
    website_company2_report: str
    linkedin_company2_report: str
    financial_company2_report: str
    # Unified analysis
    final_unified_report: str

class UnifiedCompanyComparator:

    def __init__(self, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
        self.api_key = api_key
        self.model = model
        self.llm = LLMClient(api_key=api_key, model=model or None)
        print(f"UnifiedCompanyComparator using model: {self.llm.model}")
    
    def run_website_analysis(self, state: UnifiedComparisonState) -> UnifiedComparisonState:
        """Run website comparison analysis and extract final report"""
        print("Starting Website Intelligence Analysis...")
        
        try:
            website_result = run_website_comparison(
                state["company1_website"], 
                state["company2_website"],
                use_predefined_data=state.get("use_predefined_data", False),
                company1_name=state["company1_name"],
                api_key=self.api_key,
                model=self.model,
            )
            
            
            state["website_final_report"] = website_result.get("final_report", "No website report available")
            state["website_company2_report"] = website_result.get("company2_individual_report", "No individual website report available")
            print("Website analysis completed!")
        except Exception as e:
            print(f"Website analysis failed: {e}")
            state["website_final_report"] = f"Website analysis failed: {str(e)}"
        
        return state
    
    def run_linkedin_analysis(self, state: UnifiedComparisonState) -> UnifiedComparisonState:
        """Run LinkedIn comparison analysis and extract final report"""
        print("Starting LinkedIn Intelligence Analysis...")
        
        try:
            linkedin_result = run_linkedin_comparison(
                state["company1_linkedin"],
                state["company2_linkedin"],
                use_predefined_data=state.get("use_predefined_data", False),
                company1_name=state["company1_name"],
                api_key=self.api_key,
                model=self.model,
            )
            
           
            state["linkedin_final_report"] = linkedin_result.get("final_report", "No LinkedIn report available")
            state["linkedin_company2_report"] = linkedin_result.get("company2_individual_report", "No individual LinkedIn report available")
            print("LinkedIn analysis completed!")
        except Exception as e:
            print(f"LinkedIn analysis failed: {e}")
            state["linkedin_final_report"] = f"LinkedIn analysis failed: {str(e)}"
        
        return state
    
    def run_financial_analysis(self, state: UnifiedComparisonState) -> UnifiedComparisonState:
        """Run financial comparison analysis and extract final report"""
        print("Starting Financial Intelligence Analysis...")
        
        try:
            financial_result = run_financial_comparison(
                state["company1_name"],
                state["company2_name"],
                use_predefined_data=state["use_predefined_data"],
                api_key=self.api_key,
                model=self.model,
            )
            
            
            state["financial_final_report"] = financial_result.get("final_financial_report", "No financial report available")
            state["financial_company2_report"] = financial_result.get("company2_individual_report", "No individual financial report available")
            print("Financial analysis completed!")
        except Exception as e:
            print(f"Financial analysis failed: {e}")
            state["financial_final_report"] = f"Financial analysis failed: {str(e)}"
        
        return state
    

    def generate_final_unified_report(self, state: UnifiedComparisonState) -> UnifiedComparisonState:
        """Generate the final 2-page comprehensive report without financial metrics"""
        print("Generating final unified report from comprehensive analyses...")
        
        report_prompt = f"""
        As a Master Business Intelligence Analyst, create a comprehensive 2-page unified comparison report 
        using ONLY the final comprehensive reports from three specialized analysis agents.

        COMPANIES ANALYZED:
        • {state['company1_name']} (Website: {state['company1_website']}, LinkedIn: {state['company1_linkedin']})
        • {state['company2_name']} (Website: {state['company2_website']}, LinkedIn: {state['company2_linkedin']})

        DATA SOURCES (Final Comprehensive Reports Only):
        
        1. WEBSITE INTELLIGENCE FINAL REPORT:
        {state['website_final_report']}
        
        2. LINKEDIN INTELLIGENCE FINAL REPORT:
        {state['linkedin_final_report']}
        
        3. FINANCIAL INTELLIGENCE FINAL REPORT:
        {state['financial_final_report']}

        Generate a professionally formatted business intelligence report with the following EXACT structure:

        ================================================================================
                                COMPREHENSIVE COMPANY COMPARISON REPORT
        ================================================================================
        
        EXECUTIVE SUMMARY
        =================
        [Provide a concise 150-word summary highlighting key findings and strategic positioning]

        COMPARATIVE ANALYSIS FRAMEWORK
        ==============================
        
        1.0 DIGITAL PRESENCE & ONLINE STRATEGY
        ======================================
        1.1 Website Capability Comparison
        1.2 Digital Marketing Effectiveness
        1.3 Online Brand Positioning

        2.0 SOCIAL INTELLIGENCE & EMPLOYER BRANDING
        ===========================================
        2.1 LinkedIn Presence & Engagement
        2.2 Talent Acquisition Strategy
        2.3 Corporate Reputation & Thought Leadership

        3.0 BUSINESS FUNDAMENTALS ASSESSMENT
        ====================================
        3.1 Operational Efficiency
        3.2 Strategic Positioning
        3.3 Growth Trajectory

        4.0 COMPETITIVE ADVANTAGE MATRIX
        ================================
        4.1 Strengths & Capabilities Comparison
        4.2 Market Differentiation
        4.3 Strategic Positioning

        5.0 STRATEGIC RECOMMENDATIONS
        =============================
        5.1 For {state['company1_name']}
        5.2 For {state['company2_name']}

        6.0 CONCLUSION & STRATEGIC INSIGHTS
        ===================================
        6.1 Overall Competitive Assessment
        6.2 Future Outlook & Considerations

        7.0 DATA SOURCES
        ===================================
        7.1 Website: {state['company1_website']}, LinkedIn: {state['company1_linkedin']}
        7.2 Website: {state['company2_website']}, LinkedIn: {state['company2_linkedin']}


        **CRITICAL FORMATTING RULES:**
        1. Use href links for specific evidence supporting MAJOR findings
        2. For website capabilities: Reference specific pages like <a href="{state['company1_website']}/services" target="_blank">{state['company1_name']} Services</a>
        3. For LinkedIn presence: Reference specific sections like <a href="{state['company2_linkedin']}/about" target="_blank">{state['company2_name']} LinkedIn About</a>
        4. For content strategy: Reference posts pages like <a href="{state['company1_linkedin']}/posts" target="_blank">{state['company1_name']} LinkedIn Posts</a>
        5. Maximum 5 href links in the entire report should be present
        6. Minimum 2 href links in the entire report should be mandatorily present
        7. Links should go to the most significant evidence sources that support key differentiators

        **EXAMPLES OF SPECIFIC URL INTEGRATION:**
            Regular analysis points:
            - "Company A shows stronger technical capabilities in their service offerings"
            - "Both companies demonstrate active LinkedIn engagement strategies"

            MAJOR findings with URL support (use sparingly):
            - "Company A demonstrates superior digital presence, particularly in their comprehensive service documentation found at <a href="{state['company1_website']}/services" target="_blank">{state['company1_name']} Services Page</a>"
            - "The core competitive advantage for Company B lies in their specialized AI offerings detailed at <a href="{state['company2_website']}/ai-solutions" target="_blank">{state['company2_name']} AI Solutions</a>"
            - "Critical differentiation is evident in Company A's hiring strategy reflected in their active job postings at <a href="{state['company1_linkedin']}/jobs" target="_blank">{state['company1_name']} LinkedIn Jobs</a>"
            - "Company B's thought leadership is demonstrated through their consistent content updates visible at <a href="{state['company2_linkedin']}/posts" target="_blank">{state['company2_name']} LinkedIn Posts</a>"

        **RESTRICTIONS:**
        - MINIMUM 2 href links in entire report - Mandatory
        - MAXIMUM 5 href links in entire report
        - Only for most significant competitive differentiators
        - Link to specific pages that provide evidence for major claims
        - No numerical metrics in the report
        - No made-up data - only reference pages that exist in the analysis
        
        **URL INTEGRATION RULES:**
        1. Use EXACTLY 5 href links in the entire report - no more, no less
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


        CRITICAL FORMATTING REQUIREMENTS:
        - DO NOT include any financial metrics, numbers
        - Use consistent comparative language throughout
        - Focus on qualitative assessments and relative positioning
        - Maintain the exact section structure above
        - Use descriptive terms instead of numerical comparisons
        - Ensure professional business language
        - Provide balanced, objective comparisons

        CONSISTENCY REQUIREMENTS:
        - Maintain consistent reporting structure across all analyses
        - Use standardized comparative language
        - Avoid numerical metrics, focus on qualitative descriptions
        - Ensure balanced, objective assessments
        - Follow the exact section formatting provided

        RULES:
        - Report only based on what exists in scraped data
        - NO guesses, or placeholder content
        - NO creative writing or embellishment  
        - NO false information of any kind
        - Every analytical conclusion must include its data justification within the same context

        Focus on creating a structured, professional business report with consistent qualitative comparisons.
        """

        state["final_unified_report"] = self.llm.generate(report_prompt)
        return state

def create_company2_individual_word_document(content, title, company2_name, session_id=None, report_type="", sources=None):
    """Create a professionally formatted Word document for Company 2 individual reports with proper structure"""
    doc = Document()
    
    # Set document properties
    doc.core_properties.title = f"{title} - {company2_name}"
    doc.core_properties.author = "Business Intelligence Tool"
    doc.core_properties.subject = f"{report_type.capitalize()} Analysis"
    
    # ========== TITLE PAGE ==========
    title_paragraph = doc.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_paragraph.add_run(title)
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(0, 0, 128)
    title_run.bold = True
    
    doc.add_paragraph()
    
    
    company_name_paragraph = doc.add_paragraph()
    company_name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    company_name_run = company_name_paragraph.add_run(company2_name)
    company_name_run.font.size = Pt(16)
    company_name_run.font.color.rgb = RGBColor(64, 64, 64)
    company_name_run.bold = True
    
    doc.add_paragraph()
    
    date_paragraph = doc.add_paragraph()
    date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_run = date_paragraph.add_run(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    date_run.font.size = Pt(12)
    date_run.font.color.rgb = RGBColor(128, 128, 128)
    
    # ========== TABLE OF CONTENTS PAGE ==========
    doc.add_page_break()
    toc_heading = doc.add_heading('TABLE OF CONTENTS', level=1)
    toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Process content for TOC - extract main sections only
    lines = content.split('\n')
    toc_sections = []
    seen_section_numbers = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip separators and tables
        if re.match(r'^[|=+-]+$', line) or line.startswith('|'):
            continue
            
        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        
        # Detect ONLY main numbered sections for TOC (1.0, 2.0, etc.)
        section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if section_match:
            section_num = section_match.group(1)
            # Only add main sections (X.0) to TOC, not subsections
            if section_num.endswith('.0') and section_num not in seen_section_numbers:
                toc_sections.append(clean_line)
                seen_section_numbers.add(section_num)
                continue
    
    # Add TOC entries with proper formatting
    for section in toc_sections:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.add_run(section)
    
    # ========== MAIN CONTENT ==========
    doc.add_page_break()
    
    def _add_hyperlink(paragraph, text, url):
        """Add a hyperlink to a paragraph"""
        part = paragraph.part
        r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
        
        hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
        hyperlink.set(docx.oxml.shared.qn('r:id'), r_id)
        
        new_run = docx.oxml.shared.OxmlElement('w:r')
        rPr = docx.oxml.shared.OxmlElement('w:rPr')
        
        # Add color
        color = docx.oxml.shared.OxmlElement('w:color')
        color.set(docx.oxml.shared.qn('w:val'), '0000FF')
        rPr.append(color)
        
        # Add underline
        underline = docx.oxml.shared.OxmlElement('w:u')
        underline.set(docx.oxml.shared.qn('w:val'), 'single')
        rPr.append(underline)
        
        new_run.append(rPr)
        new_run.text = text
        hyperlink.append(new_run)
        
        paragraph._p.append(hyperlink)
        
        return hyperlink

    def _process_text_with_hyperlinks(paragraph, text):
        """Process text and convert HTML links to Word hyperlinks"""
        link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
        
        parts = re.split(link_pattern, text)
        
        for i in range(0, len(parts), 3):
            if i < len(parts):
                # Add regular text before link
                if parts[i]:
                    paragraph.add_run(parts[i])
            
            if i + 2 < len(parts):
                # Add hyperlink
                url = parts[i + 1]
                link_text = parts[i + 2]
                _add_hyperlink(paragraph, link_text, url)
    
    current_table_lines = []
    in_table = False
    content_processed = False
    processed_sections = set()
    current_main_section = None
    current_subsection = None
    content_buffer = []
    
    executive_summary_completed = False
    first_section_processed = False
    
    def _flush_content_buffer():
        """Helper function to flush accumulated content to the document"""
        nonlocal content_buffer
        if content_buffer:
            for content_line in content_buffer:
                if content_line.strip():
                    # Check if this line contains hyperlinks
                    if '<a href=' in content_line:
                        p = doc.add_paragraph()
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
                        _process_text_with_hyperlinks(p, content_line.strip())
                    else:
                        p = doc.add_paragraph(content_line.strip())
                        p.style = 'Normal'
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
            content_buffer = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            if not in_table and content_buffer:
                content_buffer.append("")
            continue
            
        # Handle tables
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                _flush_content_buffer()
                in_table = True
                current_table_lines = []
            current_table_lines.append(line)
            continue
        elif in_table and current_table_lines and not line.startswith('|'):
            _add_table_to_document(doc, current_table_lines)
            current_table_lines = []
            in_table = False
        
        # Skip separator lines
        if re.match(r'^[|=+-]+$', line):
            continue
            
        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        
        # Skip table of contents header
        if 'TABLE OF CONTENTS' in clean_line and clean_line.isupper():
            continue
            
        # Skip main report header
        if (clean_line.isupper() and len(clean_line) > 20 and 'REPORT' in clean_line and not content_processed):
            content_processed = True
            continue
            
        # Skip duplicate section headers
        if (executive_summary_completed and 
            re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', clean_line) and
            i + 1 < len(lines) and
            re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', lines[i + 1].strip())):
            continue
            
        # EXECUTIVE SUMMARY as main section
        if clean_line.isupper() and 'EXECUTIVE SUMMARY' in clean_line:
            if 'EXECUTIVE SUMMARY' not in processed_sections:
                _flush_content_buffer()
                doc.add_heading(clean_line, level=1)
                processed_sections.add('EXECUTIVE SUMMARY')
                current_main_section = 'EXECUTIVE SUMMARY'
                current_subsection = None
                executive_summary_completed = False
                first_section_processed = False
            continue
            
        # Main section headers (1.0, 2.0, etc.)
        main_section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if main_section_match:
            section_id = main_section_match.group(1)
            section_title = main_section_match.group(2)
            
            if (section_id == "7.0" and "Strategic Recommendations" in section_title and
                current_main_section == 'EXECUTIVE SUMMARY' and not first_section_processed):
                continue

            if (section_id == "7.0" and "Conclusion & Key Insights" in section_title and
                current_main_section == 'EXECUTIVE SUMMARY' and not first_section_processed):
                continue

            if (current_main_section == 'EXECUTIVE SUMMARY' and 
                section_id.endswith('.0') and
                i + 1 < len(lines) and 
                re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', lines[i + 1].strip())):
                executive_summary_completed = True
                continue
                
            _flush_content_buffer()
            # Add the main section heading
            doc.add_heading(clean_line, level=1)
            processed_sections.add(section_id)
            current_main_section = section_id
            current_subsection = None
            first_section_processed = True
            continue
            
        # Subsection headers (1.1, 2.1, 2.2, etc.)
        subsection_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if subsection_match:
            section_num = subsection_match.group(1)
            
            if not section_num.endswith('.0'):
                _flush_content_buffer()
                doc.add_heading(clean_line, level=2)
                current_subsection = section_num
            continue
            
        # Bullet points
        if clean_line.startswith('•') or clean_line.startswith('-'):
            _flush_content_buffer()
            p = doc.add_paragraph()
            p.style = 'List Bullet'
            p.paragraph_format.left_indent = Pt(36)
            p.paragraph_format.space_after = Pt(6)
            
            if '<a href=' in clean_line:
                _process_text_with_hyperlinks(p, clean_line[1:].strip())
            else:
                p.add_run(clean_line[1:].strip())
            continue
            
        # Numbered lists
        numbered_match = re.match(r'^(\d+\.)\s+(.+)$', clean_line)
        if numbered_match:
            _flush_content_buffer()
            p = doc.add_paragraph()
            p.style = 'List Number'
            p.paragraph_format.left_indent = Pt(36)
            p.paragraph_format.space_after = Pt(6)
            
            if '<a href=' in clean_line:
                _process_text_with_hyperlinks(p, clean_line)
            else:
                p.add_run(clean_line)
            continue
            
        # Regular content
        if len(clean_line) > 5 and not clean_line.isupper():
            if (clean_line not in toc_sections and 
                clean_line not in processed_sections and
                not re.match(r'^\d+\.\d+\s+.+$', clean_line)):
                content_buffer.append(clean_line)
    
    # Flush any remaining content
    _flush_content_buffer()
    if in_table and current_table_lines:
        _add_table_to_document(doc, current_table_lines)
    
    # ========== SOURCES & REFERENCES PAGE ==========
    if sources:
        doc.add_page_break()
        sources_heading = doc.add_heading('SOURCES & REFERENCES', level=1)
        sources_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        intro = doc.add_paragraph('The following sources were used to gather data for this analysis:')
        intro.paragraph_format.space_after = Pt(12)
        for i, url in enumerate(sources, 1):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.add_run(f"[{i}] ")
            _add_hyperlink(p, url, url)

    # ========== COMPANY 2 SPECIFIC METADATA PAGE ==========
    doc.add_page_break()
    metadata_heading = doc.add_heading('REPORT METADATA & DETAILS', level=1)
    metadata_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    metadata_info = [
        ("Report Title", title),
        ("Company Analyzed", company2_name),
        ("Report Type", f"Individual {report_type.capitalize()} Analysis"),
        ("Analysis Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ("Session ID", session_id if session_id else "N/A"),
        ("Data Sources", f"{report_type.capitalize()} Intelligence Analysis"),
        ("Analysis Framework", "Multi-Agent AI Analysis with LangGraph"),
        ("Report Format", "Microsoft Word Document (.docx)"),
        ("Generated By", "Business Intelligence Tool")
    ]
    
    for label, value in metadata_info:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        label_run = p.add_run(f"{label}: ")
        label_run.bold = True
        label_run.font.color.rgb = RGBColor(0, 0, 128) 
        p.add_run(value)
    
    return doc

def create_professional_word_document(content, title, company1, company2, session_id=None):
    """Create a professionally formatted Word document with proper structure and hyperlinks"""
    doc = Document()
    
    # Set document properties
    doc.core_properties.title = f"{title} - {company1} vs {company2}"
    doc.core_properties.author = "Business Intelligence Tool"
    
    # ========== TITLE PAGE ==========
    title_paragraph = doc.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_paragraph.add_run(title)
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(0, 0, 128)
    title_run.bold = True
    
    doc.add_paragraph()
    
    companies_paragraph = doc.add_paragraph()
    companies_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    companies_run = companies_paragraph.add_run(f"{company1} vs {company2}")
    companies_run.font.size = Pt(16)
    companies_run.font.color.rgb = RGBColor(64, 64, 64)
    
    doc.add_paragraph()
    
    date_paragraph = doc.add_paragraph()
    date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_run = date_paragraph.add_run(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    date_run.font.size = Pt(12)
    date_run.font.color.rgb = RGBColor(128, 128, 128)
    
    # ========== TABLE OF CONTENTS PAGE ==========
    doc.add_page_break()
    toc_heading = doc.add_heading('TABLE OF CONTENTS', level=1)
    toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Process content for TOC - extract main sections only
    lines = content.split('\n')
    toc_sections = []
    seen_section_numbers = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip separators and tables
        if re.match(r'^[|=+-]+$', line) or line.startswith('|'):
            continue
            
        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        
        # Detect ONLY main numbered sections for TOC (1.0, 2.0, etc.)
        section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if section_match:
            section_num = section_match.group(1)
            # Only add main sections (X.0) to TOC, not subsections
            if section_num.endswith('.0') and section_num not in seen_section_numbers:
                toc_sections.append(clean_line)
                seen_section_numbers.add(section_num)
                continue
    
    # Add TOC entries with proper formatting
    for section in toc_sections:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.add_run(section)
    
    # ========== MAIN CONTENT ==========
    doc.add_page_break()
    
    def _add_hyperlink(paragraph, text, url):
        """Add a hyperlink to a paragraph"""
        # This creates the hyperlink field
        part = paragraph.part
        r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
        
        # Create the hyperlink run
        hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
        hyperlink.set(docx.oxml.shared.qn('r:id'), r_id)
        
        # Create a new run for the hyperlink text
        new_run = docx.oxml.shared.OxmlElement('w:r')
        rPr = docx.oxml.shared.OxmlElement('w:rPr')
        
        # Add color
        color = docx.oxml.shared.OxmlElement('w:color')
        color.set(docx.oxml.shared.qn('w:val'), '0000FF')
        rPr.append(color)
        
        # Add underline
        underline = docx.oxml.shared.OxmlElement('w:u')
        underline.set(docx.oxml.shared.qn('w:val'), 'single')
        rPr.append(underline)
        
        new_run.append(rPr)
        new_run.text = text
        hyperlink.append(new_run)
        
        paragraph._p.append(hyperlink)
        
        return hyperlink

    def _process_text_with_hyperlinks(paragraph, text):
        """Process text and convert HTML links to Word hyperlinks"""
        # Pattern to match <a href="URL" target="_blank">Link Text</a>
        link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
        
        parts = re.split(link_pattern, text)
        
        for i in range(0, len(parts), 3):
            if i < len(parts):
                # Add regular text before link
                if parts[i]:
                    paragraph.add_run(parts[i])
            
            if i + 2 < len(parts):
                # Add hyperlink
                url = parts[i + 1]
                link_text = parts[i + 2]
                _add_hyperlink(paragraph, link_text, url)
    
    current_table_lines = []
    in_table = False
    content_processed = False
    processed_sections = set()
    current_main_section = None
    current_subsection = None
    content_buffer = []
    
    executive_summary_completed = False
    first_section_processed = False
    
    def _flush_content_buffer():
        """Helper function to flush accumulated content to the document"""
        nonlocal content_buffer
        if content_buffer:
            for content_line in content_buffer:
                if content_line.strip():
                    # Check if this line contains hyperlinks
                    if '<a href=' in content_line:
                        p = doc.add_paragraph()
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
                        _process_text_with_hyperlinks(p, content_line.strip())
                    else:
                        p = doc.add_paragraph(content_line.strip())
                        p.style = 'Normal'
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.15
            content_buffer = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            if not in_table and content_buffer:
                content_buffer.append("")
            continue
            
        # Handle tables
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                _flush_content_buffer()
                in_table = True
                current_table_lines = []
            current_table_lines.append(line)
            continue
        elif in_table and current_table_lines and not line.startswith('|'):
            _add_table_to_document(doc, current_table_lines)
            current_table_lines = []
            in_table = False
        
        # Skip separator lines
        if re.match(r'^[|=+-]+$', line):
            continue
            
        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        
        # Skip table of contents header
        if 'TABLE OF CONTENTS' in clean_line and clean_line.isupper():
            continue
            
        # Skip main report header
        if (clean_line.isupper() and len(clean_line) > 20 and 'REPORT' in clean_line and not content_processed):
            content_processed = True
            continue
            
        # Skip duplicate section headers
        if (executive_summary_completed and 
            re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', clean_line) and
            i + 1 < len(lines) and
            re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', lines[i + 1].strip())):
            continue
            
        # EXECUTIVE SUMMARY as main section
        if clean_line.isupper() and 'EXECUTIVE SUMMARY' in clean_line:
            if 'EXECUTIVE SUMMARY' not in processed_sections:
                _flush_content_buffer()
                doc.add_heading(clean_line, level=1)
                processed_sections.add('EXECUTIVE SUMMARY')
                current_main_section = 'EXECUTIVE SUMMARY'
                current_subsection = None
                executive_summary_completed = False
                first_section_processed = False
            continue
            
        # Main section headers (1.0, 2.0, etc.)
        main_section_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if main_section_match:
            section_id = main_section_match.group(1)
            section_title = main_section_match.group(2)
            
            if (section_id == "7.0" and "Strategic Recommendations" in section_title and
                current_main_section == 'EXECUTIVE SUMMARY' and not first_section_processed):
                continue

            if (section_id == "7.0" and "Conclusion & Key Insights" in section_title and
                current_main_section == 'EXECUTIVE SUMMARY' and not first_section_processed):
                continue

            if (current_main_section == 'EXECUTIVE SUMMARY' and 
                section_id.endswith('.0') and
                i + 1 < len(lines) and 
                re.match(r'^\d+\.\d+\s+[A-Za-z& ]+$', lines[i + 1].strip())):
                executive_summary_completed = True
                continue
                
            _flush_content_buffer()
            # Add the main section heading
            doc.add_heading(clean_line, level=1)
            processed_sections.add(section_id)
            current_main_section = section_id
            current_subsection = None
            first_section_processed = True
            continue
            
        # Subsection headers (1.1, 2.1, 2.2, etc.)
        subsection_match = re.match(r'^(\d+\.\d+)\s+(.+)$', clean_line)
        if subsection_match:
            section_num = subsection_match.group(1)
            
            if not section_num.endswith('.0'):
                _flush_content_buffer()
                doc.add_heading(clean_line, level=2)
                current_subsection = section_num
            continue
            
        # Bullet points
        if clean_line.startswith('•') or clean_line.startswith('-'):
            _flush_content_buffer()
            p = doc.add_paragraph()
            p.style = 'List Bullet'
            p.paragraph_format.left_indent = Pt(36)
            p.paragraph_format.space_after = Pt(6)
            
            if '<a href=' in clean_line:
                _process_text_with_hyperlinks(p, clean_line[1:].strip())
            else:
                p.add_run(clean_line[1:].strip())
            continue
            
        # Numbered lists
        numbered_match = re.match(r'^(\d+\.)\s+(.+)$', clean_line)
        if numbered_match:
            _flush_content_buffer()
            p = doc.add_paragraph()
            p.style = 'List Number'
            p.paragraph_format.left_indent = Pt(36)
            p.paragraph_format.space_after = Pt(6)
            
            if '<a href=' in clean_line:
                _process_text_with_hyperlinks(p, clean_line)
            else:
                p.add_run(clean_line)
            continue
            
        # Regular content
        if len(clean_line) > 5 and not clean_line.isupper():
            if (clean_line not in toc_sections and 
                clean_line not in processed_sections and
                not re.match(r'^\d+\.\d+\s+.+$', clean_line)):
                content_buffer.append(clean_line)
    
    # Flush any remaining content
    _flush_content_buffer()
    if in_table and current_table_lines:
        _add_table_to_document(doc, current_table_lines)
    
    # ========== METADATA PAGE ==========
    doc.add_page_break()
    metadata_heading = doc.add_heading('REPORT METADATA & DETAILS', level=1)
    metadata_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    metadata_info = [
        ("Report Title", title),
        ("Companies Analyzed", f"{company1} vs {company2}"),
        ("Analysis Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ("Session ID", session_id if session_id else "N/A"),
        ("Data Sources", "Website Intelligence + LinkedIn Analysis + Financial Data"),
        ("Analysis Framework", "Multi-Agent AI Analysis with LangGraph"),
        ("Report Format", "Microsoft Word Document (.docx)"),
        ("Generated By", "Business Intelligence Tool")
    ]
    
    for label, value in metadata_info:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        label_run = p.add_run(f"{label}: ")
        label_run.bold = True
        p.add_run(value)
    
    return doc
def _add_table_to_document(doc, table_lines):
    """Add a properly formatted table to the Word document"""
    if len(table_lines) < 2:
        return
    
    # Parse table data and clean markdown formatting
    table_data = []
    for line in table_lines:
        
        cells = [cell.strip() for cell in line.strip('|').split('|')]
       
        clean_cells = [re.sub(r'\*\*([^*]+)\*\*', r'\1', cell) for cell in cells if cell.strip()]
        
        if clean_cells and any(cell.strip() for cell in clean_cells):
            table_data.append(clean_cells)
    
    if len(table_data) < 2:  
        return
    
    
    table_data = [row for row in table_data if not all(re.match(r'^[\s-]*$', cell) for cell in row)]
    
    if len(table_data) < 2:
        return
    
    # Create table
    num_rows = len(table_data)
    num_cols = max(len(row) for row in table_data)  
    
    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.style = 'Table Grid'
    
    # Populate table with formatting
    for i, row in enumerate(table_data):
        for j in range(num_cols):
            cell_content = row[j] if j < len(row) else ""
            clean_content = re.sub(r'^[-|\s]+$', '', cell_content)  
            
            if clean_content.strip():
                table.cell(i, j).text = clean_content.strip()
                
                # Header row formatting (first row)
                if i == 0:
                    table.cell(i, j).paragraphs[0].runs[0].bold = True
                    table.cell(i, j).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    
                    cell_text = clean_content.strip().upper()
                    if any(indicator in cell_text for indicator in ['HIGH', 'GOOD', 'STRONG', 'BUY', 'POSITIVE']):
                        table.cell(i, j).paragraphs[0].runs[0].bold = True
                        table.cell(i, j).paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 128, 0)  # Green
                    elif any(indicator in cell_text for indicator in ['LOW', 'POOR', 'WEAK', 'SELL', 'NEGATIVE']):
                        table.cell(i, j).paragraphs[0].runs[0].bold = True
                        table.cell(i, j).paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 0, 0)  # Red
    
    # Add spacing after table
    doc.add_paragraph()
    
def create_unified_comparison_workflow(api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Create the unified LangGraph workflow using only final reports"""
    workflow = StateGraph(UnifiedComparisonState)
    
    unified_comparator = UnifiedCompanyComparator(api_key=api_key, model=model)
    
    
    workflow.add_node("run_website_analysis", unified_comparator.run_website_analysis)
    workflow.add_node("run_linkedin_analysis", unified_comparator.run_linkedin_analysis)
    workflow.add_node("run_financial_analysis", unified_comparator.run_financial_analysis)
    
    # Add node for final unified report generation
    workflow.add_node("generate_final_report", unified_comparator.generate_final_unified_report)
    
    # Define workflow - run all analyses then generate unified report
    workflow.set_entry_point("run_website_analysis")
    workflow.add_edge("run_website_analysis", "run_linkedin_analysis")
    workflow.add_edge("run_linkedin_analysis", "run_financial_analysis")
    workflow.add_edge("run_financial_analysis", "generate_final_report")
    workflow.add_edge("generate_final_report", END)
    
    return workflow.compile()

def run_unified_comparison(company1_name, company2_name, company1_website, company2_website, company1_linkedin, company2_linkedin, session_id=None, use_predefined_data=False, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Run the complete unified comparison using only final reports"""
    workflow = create_unified_comparison_workflow(api_key=api_key, model=model)
    
    initial_state = {
        "company1_name": company1_name,
        "company2_name": company2_name,
        "company1_website": company1_website,
        "company2_website": company2_website,
        "company1_linkedin": company1_linkedin,
        "company2_linkedin": company2_linkedin,
        "website_final_report": "",
        "linkedin_final_report": "",
        "financial_final_report": "",
        "final_unified_report": "",
        "website_company2_report": "",
        "linkedin_company2_report": "",
        "financial_company2_report": "",
        "session_id": session_id,
        "use_predefined_data": use_predefined_data,
    }
    
    result = workflow.invoke(initial_state)
    if session_id:
        unified_filename = os.path.join(REPORTS_DIR, f"unified_company_comparison_report_{session_id}.docx")
        website_filename = os.path.join(REPORTS_DIR, f"website_final_report_{session_id}.docx")
        linkedin_filename = os.path.join(REPORTS_DIR, f"linkedin_final_report_{session_id}.docx")
        financial_filename = os.path.join(REPORTS_DIR, f"financial_final_report_{session_id}.docx")
    else:
        unified_filename = os.path.join(REPORTS_DIR, "unified_company_comparison_report.docx")
        website_filename = os.path.join(REPORTS_DIR, "website_final_report.docx")
        linkedin_filename = os.path.join(REPORTS_DIR, "linkedin_final_report.docx")
        financial_filename = os.path.join(REPORTS_DIR, "financial_final_report.docx")
    
    # Save reports with proper formatting - ONLY ONCE
    try:
        # Unified Report
        unified_doc = create_professional_word_document(
            result["final_unified_report"],
            "COMPREHENSIVE COMPANY COMPARISON REPORT",
            company1_name,
            company2_name,
            session_id
        )
        unified_doc.save(unified_filename)
        print(f"Saved final report to {os.path.abspath(unified_filename)}")
        
        
        website_content = result["website_company2_report"]
        website_doc = create_company2_individual_word_document(
            website_content,
            f"WEBSITE ANALYSIS REPORT",
            company2_name,
            session_id,
            "website",
            sources=[company2_website, f"{company2_website.rstrip('/')}/about",
                     f"{company2_website.rstrip('/')}/services", company2_linkedin]
        )
        website_doc.save(website_filename)
      
        linkedin_content = result["linkedin_company2_report"]
        linkedin_doc = create_company2_individual_word_document(
            linkedin_content,
            f"LINKEDIN ANALYSIS REPORT",
            company2_name,
            session_id,
            "linkedin",
            sources=[company2_linkedin, f"{company2_linkedin.rstrip('/')}/about",
                     f"{company2_linkedin.rstrip('/')}/posts", f"{company2_linkedin.rstrip('/')}/jobs"]
        )
        linkedin_doc.save(linkedin_filename)
        
        financial_content = result["financial_company2_report"]
        financial_doc = create_company2_individual_word_document(
            financial_content,
            f"FINANCIAL ANALYSIS REPORT",
            company2_name,
            session_id,
            "financial",
            sources=[company2_website,
                     f"https://finance.yahoo.com/quote/{company2_name.upper().replace(' ', '')}",
                     f"{company2_website.rstrip('/')}/investors",
                     f"https://www.macrotrends.net/stocks/charts/{company2_name.lower().replace(' ', '-')}/revenue"]
        )
        financial_doc.save(financial_filename)
       
        
    except Exception as e:
        print(f"Error saving Word documents: {e}")
        # Fallback to simple text saving
        with open(unified_filename.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
            f.write(result["final_unified_report"])
    
    return {
        "final_unified_report": result["final_unified_report"],
        "website_final_report": result["website_final_report"], 
        "linkedin_final_report": result["linkedin_final_report"],
        "financial_final_report": result["financial_final_report"],
        "website_company2_report": result["website_company2_report"],
        "linkedin_company2_report": result["linkedin_company2_report"],
        "financial_company2_report": result["financial_company2_report"],
        "session_id": session_id,
        "company1_name": company1_name,
        "company2_name": company2_name
    }

def main():
    import time
    
    print("UNIFIED COMPANY COMPARISON INTELLIGENCE PLATFORM")
    print("=" * 70)
    print("This system integrates final comprehensive reports from:")
    print("• Website Analysis • LinkedIn Intelligence • Financial Analysis")
    print("=" * 70)
    
    try:
        # Get user input
        print("\nENTER COMPANY DETAILS:")
        company1_name = input("First Company Name: ").strip()
        company1_website = input("First Company Website URL: ").strip()
        company1_linkedin = input("First Company LinkedIn URL: ").strip()
        
        print("\n" + "-" * 50)
        
        company2_name = input("Second Company Name: ").strip()
        company2_website = input("Second Company Website URL: ").strip()
        company2_linkedin = input("Second Company LinkedIn URL: ").strip()
        
        # Validate inputs
        if not all([company1_name, company2_name, company1_website, company2_website, company1_linkedin, company2_linkedin]):
            print("Please provide all required information.")
            return
        
        # Format URLs if needed
        if not company1_website.startswith(('http://', 'https://')):
            company1_website = 'https://' + company1_website
        if not company2_website.startswith(('http://', 'https://')):
            company2_website = 'https://' + company2_website
        
        print(f"\nUNIFIED ANALYSIS REQUEST:")
        print(f"   {company1_name}:")
        print(f"     Website: {company1_website}")
        print(f"     LinkedIn: {company1_linkedin}")
        print(f"   {company2_name}:")
        print(f"     Website: {company2_website}")
        print(f"     LinkedIn: {company2_linkedin}")
        
        print("\nThis may take 5-10 minutes...")
        print("   (Running comprehensive multi-source intelligence analysis)\n")
        
        # Perform unified comparison
        start_time = time.time()
        result = run_unified_comparison(
            company1_name, company2_name,
            company1_website, company2_website,
            company1_linkedin, company2_linkedin
        )
        end_time = time.time()
        
        print(f"Unified analysis completed in {end_time - start_time:.1f} seconds")
        
        # Show preview of the unified report
        print("\nUNIFIED REPORT PREVIEW:")
        print("=" * 70)
        lines = result["final_unified_report"].split('\n')
        for line in lines[:20]:  
            print(line)
        print("=" * 70)
        
        print(f"\nUNIFIED INTELLIGENCE ANALYSIS COMPLETED!")
        print(f"Unified 2-page report: unified_company_comparison_report.docx")
        print(f"Individual final reports also saved:")
        print(f"   • Website: website_final_report.docx")
        print(f"   • LinkedIn: linkedin_final_report.docx") 
        print(f"   • Financial: financial_final_report.docx")
        print(f"Analysis method: Final comprehensive reports synthesis")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check all URLs are accessible")
        print("2. Ensure company names are accurate")
        print("3. Verify internet connectivity")
        print("4. Check API key validity")

if __name__ == "__main__":
    main()