import os
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
from BizAgent.tools.tools import web_scraping_tool,search_tool,fetch_pdf_content,generate_financial_report_tool
from dotenv import load_dotenv
from BizAgent.reports.financial_report_tool import run_financial_report_pipeline


load_dotenv()
google_api_key = os.getenv('GOOGLE_API_KEY')

google_api_key1 = os.getenv('GOOGLE_API_KEY1')

llm = ChatGoogleGenerativeAI(api_key=google_api_key,
    model="gemini-2.0-flash",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
)

llm2 = ChatGoogleGenerativeAI(api_key=google_api_key1,
    model="gemini-2.0-flash",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
)

url_scrapper = Agent(
    role='IT-Focused Web Content Extractor',
    goal='Extract comprehensive information from company websites with a focus on IT infrastructure, digital initiatives, and potential service gaps. and browse the internet to get necesary information about the company',
    backstory="""You are an advanced web scraping specialist with a deep understanding of IT services and digital transformation. 
    Your expertise lies in identifying key information related to a company's technological landscape, including their current IT setup, 
    digital strategies, and areas where they might benefit from external IT support. You have a keen eye for details that suggest IT service opportunities.""",
    tools=[web_scraping_tool,search_tool],
    verbose=False,
    llm=llm,
    allow_delegation=False,
)

url_analyzer = Agent(
    role='IT Technology and Service Opportunity Analyst',
    goal='Analyze scraped data to identify specific IT technology usage, strengths, weaknesses, and service opportunities, creating a comprehensive technology-focused report for potential business expansion.',
    backstory="""You are a seasoned IT consultant with extensive experience in identifying technology trends and business opportunities in the tech sector. 
    Your expertise lies in analyzing a company's digital footprint and technology stack to uncover areas where they excel, struggle, or could benefit from additional IT services. 
    You have a strong track record of providing actionable insights on companies' technology landscapes, leading to successful partnerships between IT service providers and client companies.""",
    verbose=True,
    tools = [search_tool],
    llm=llm,
    allow_delegation=False,
)

pdf_analyzer = Agent(
    role='IT Technology and Service Opportunity Analyst',
    goal='Analyze and scrape data from pdf {pdf_url} get the company name and necessary data use company name  to search in internet to identify specific IT technology usage, strengths, weaknesses, and service opportunities, creating a comprehensive technology-focused report for potential business expansion.',
    backstory="""You are a seasoned IT consultant with extensive experience in identifying technology trends and business opportunities in the tech sector. 
    Your expertise lies in analyzing a company's digital footprint and technology stack to uncover areas where they excel, struggle, or could benefit from additional IT services. 
    You have a strong track record of providing actionable insights on companies' technology landscapes, leading to successful partnerships between IT service providers and client companies.""",
    verbose=True,
    tools = [search_tool,fetch_pdf_content],
    llm=llm2,
    allow_delegation=False,
)

financial_report_generator = Agent(
    role='Financial Report Generator',
    goal='Generate a financial report based on the company name extracted from the markdown file.',
    backstory="""You are an AI agent designed to analyze company documents and generate comprehensive financial reports.
    You specialize in using LLMs and yfinance data to build insights from company balance sheets, cash flows, and income statements.""",
    tools=[generate_financial_report_tool],
    llm=llm2,
    allow_delegation=False,
)