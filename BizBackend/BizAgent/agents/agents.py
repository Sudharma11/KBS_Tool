import os
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from crewai import Agent
from dotenv import load_dotenv

from BizAgent.tools.tools import (
    web_scraping_tool,
    serpapi_search_tool,
    fetch_pdf_content,
    linkedin_insights_tool,
    generate_financial_report_tool,
    edgar_tool,
    fmp_tool,
    news_tool,
    wikipedia_company_tool,
    yahoo_finance_tool
)

load_dotenv()

# --- Language Model Configurations ---
llm_config = {"temperature": 0.2, "max_tokens": 4096}
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", **llm_config, google_api_key=os.getenv('GOOGLE_API_KEY'))
llm2 = ChatGoogleGenerativeAI(model="gemini-2.0-flash", **llm_config, google_api_key=os.getenv('GOOGLE_API_KEY1'))

# --- Agent Definitions ---

company_researcher = Agent(
    role="Senior Company Research Analyst",
    goal="Compile a detailed and structured overview of a given company.",
    backstory="An expert in gathering and synthesizing corporate information from various sources to provide a foundational understanding of a company.",
    tools=[wikipedia_company_tool, serpapi_search_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

competitor_analyst = Agent(
    role="Lead Competitive Intelligence Analyst",
    goal="Identify and analyze the key competitors of a given company to provide a strategic assessment of the competitive landscape.",
    backstory="A seasoned strategist with a deep understanding of market dynamics, excelling at uncovering competitive advantages and weaknesses.",
    tools=[serpapi_search_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

finance_analyst = Agent(
    role="Quantitative Financial Analyst",
    goal="Analyze the financial health of a company, using web search to find a ticker symbol if not provided, and then fetching detailed financial statements to answer specific, in-depth questions.",
    backstory="A meticulous financial expert skilled in interpreting financial statements. You must use the Yahoo Finance tool as your primary source for financial data.",
    tools=[yahoo_finance_tool, serpapi_search_tool, fmp_tool, edgar_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

market_analyst = Agent(
    role="Senior Market Research Analyst",
    goal="Conduct a thorough analysis of the target company's market, including size, trends, and growth opportunities.",
    backstory="A specialist in market intelligence and trend analysis, providing data-driven insights that help businesses understand their operating environment.",
    tools=[serpapi_search_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

news_gatherer = Agent(
    role="Corporate News Curator",
    goal="Gather, summarize, and analyze the most recent and impactful news related to a company.",
    backstory="A news intelligence specialist focused on providing timely and relevant information, discerning the sentiment and business impact of news articles.",
    tools=[news_tool, serpapi_search_tool],
    llm=llm, verbose=True, memory=True, allow_delegation=False,
)

url_scrapper = Agent(
    role='IT-Focused Web Content Extractor',
    goal='Extract comprehensive information from a company website and the web, focusing on IT infrastructure, digital initiatives, and potential service gaps.',
    backstory="An advanced web scraping specialist with a deep understanding of IT services and digital transformation.",
    tools=[web_scraping_tool, serpapi_search_tool],
    llm=llm, verbose=True, allow_delegation=False,
)

url_analyzer = Agent(
    role='IT, Business, and LinkedIn Strategy Analyst',
    goal='Synthesize scraped web content and provided LinkedIn insights to create a comprehensive technology and business report.',
    backstory="A seasoned consultant who combines data from multiple digital sources to identify technology trends, business opportunities, and strategic weaknesses.",
    tools=[serpapi_search_tool],
    llm=llm2, verbose=True, allow_delegation=False,
)

pdf_analyzer = Agent(
    role='IT Document Analyst',
    goal='Analyze and scrape data from a given PDF to identify IT technology usage, strengths, weaknesses, and service opportunities, supplementing with web research.',
    backstory="An expert in analyzing documents to uncover technological insights and business opportunities, leading to successful partnerships.",
    tools=[serpapi_search_tool, fetch_pdf_content],
    llm=llm, verbose=True, allow_delegation=False,
)

financial_report_generator = Agent(
    role='Lead Financial Analyst & Report Synthesizer',
    goal='Synthesize research from multiple agents to generate a comprehensive, context-aware financial report in markdown format.',
    backstory="A senior financial strategist responsible for creating the final, consolidated report, weaving together different strands of intelligence to tell a cohesive story.",
    tools=[], # This agent synthesizes, it doesn't need its own tools.
    llm=llm, verbose=True, allow_delegation=False,
)

linkedin_agent = Agent(
    role="LinkedIn Intelligence Analyst",
    goal="Fetch and analyze LinkedIn company data using the provided universal name to uncover strategic insights and sales signals.",
    backstory="An expert in corporate social media analysis, skilled at interpreting LinkedIn data to uncover hiring trends, strategic priorities, and sales signals.",
    tools=[linkedin_insights_tool, serpapi_search_tool],
    llm=llm2, verbose=True, allow_delegation=False,
)



#-------------------------------------------------------------------------------------------------
# import os
# from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
# from crewai import Agent, Task, Crew, Process
# from crewai_tools import tool
# from BizAgent.tools.tools import web_scraping_tool,search_tool,fetch_pdf_content,linkedin_insights_tool
# from dotenv import load_dotenv
# from BizAgent.reports.financial_report_tool import run_financial_report_pipeline

# load_dotenv()
# google_api_key = os.getenv('GOOGLE_API_KEY')

# google_api_key1 = os.getenv('GOOGLE_API_KEY1')

# llm = ChatGoogleGenerativeAI(api_key=google_api_key,
#     model="gemini-2.0-flash",
#     temperature=0.2,
#     max_tokens=None,
#     timeout=None,
# )

# llm2 = ChatGoogleGenerativeAI(api_key=google_api_key1,
#     model="gemini-2.0-flash",
#     temperature=0.2,
#     max_tokens=None,
#     timeout=None,
# )

# url_scrapper = Agent(
#     role='IT-Focused Web Content Extractor',
#     goal='Extract comprehensive information from company websites with a focus on IT infrastructure, digital initiatives, and potential service gaps. and browse the internet to get necesary information about the company',
#     backstory="""You are an advanced web scraping specialist with a deep understanding of IT services and digital transformation. 
#     Your expertise lies in identifying key information related to a company's technological landscape, including their current IT setup, 
#     digital strategies, and areas where they might benefit from external IT support. You have a keen eye for details that suggest IT service opportunities.""",
#     tools=[web_scraping_tool,search_tool],
#     verbose=False,
#     llm=llm,
#     allow_delegation=False,
# )

# url_analyzer = Agent(
#     role='IT Technology and Service Opportunity Analyst',
#     goal='Analyze scraped data to identify specific IT technology usage, strengths, weaknesses, and service opportunities, creating a comprehensive technology-focused report for potential business expansion.',
#     backstory="""You are a seasoned IT consultant with extensive experience in identifying technology trends and business opportunities in the tech sector. 
#     Your expertise lies in analyzing a company's digital footprint and technology stack to uncover areas where they excel, struggle, or could benefit from additional IT services. 
#     You have a strong track record of providing actionable insights on companies' technology landscapes, leading to successful partnerships between IT service providers and client companies.""",
#     verbose=True,
#     tools = [search_tool],
#     llm=llm,
#     allow_delegation=False,
# )

# pdf_analyzer = Agent(
#     role='IT Technology and Service Opportunity Analyst',
#     goal='Analyze and scrape data from pdf {pdf_url} get the company name and necessary data use company name  to search in internet to identify specific IT technology usage, strengths, weaknesses, and service opportunities, creating a comprehensive technology-focused report for potential business expansion.',
#     backstory="""You are a seasoned IT consultant with extensive experience in identifying technology trends and business opportunities in the tech sector. 
#     Your expertise lies in analyzing a company's digital footprint and technology stack to uncover areas where they excel, struggle, or could benefit from additional IT services. 
#     You have a strong track record of providing actionable insights on companies' technology landscapes, leading to successful partnerships between IT service providers and client companies.""",
#     verbose=True,
#     tools = [search_tool,fetch_pdf_content],
#     llm=llm2,
#     allow_delegation=False,
# )

# @tool("Generate Financial Report")
# def generate_financial_report_tool(company_name: str) -> str:
#     """Generates a markdown financial report for the given company using financial data."""
#     return run_financial_report_pipeline(company_name)

# financial_report_generator = Agent(
#     role='Financial Report Generator',
#     goal='Generate a financial report based on the company name extracted from the markdown file.',
#     backstory="""You are an AI agent designed to analyze company documents and generate comprehensive financial reports.
#     You specialize in using LLMs and yfinance data to build insights from company balance sheets, cash flows, and income statements.""",
#     tools=[generate_financial_report_tool],
#     llm=llm2,
#     allow_delegation=False,
# )


# linkedin_agent = Agent(
#     role="LinkedIn Insights Extractor",
#     goal="Fetch and analyze LinkedIn company data to uncover sales opportunities and signals.",
#     backstory="""You are a LinkedIn intelligence agent specializing in analyzing 
#     company profiles and recent activity. You identify growth signals, 
#     hiring patterns, partnerships, and product launches that indicate business opportunities.""",
#     tools=[linkedin_insights_tool],
#     llm=llm2,   # can use llm2 like pdf_analyzer
#     allow_delegation=False,
#     verbose=True,
# )
