import json
import os
import re
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from urllib.parse import urlparse
# Corrected: Replaced deprecated PyPDF2 with the modern pypdf library
from pypdf import PdfReader
from crewai_tools import tool
from dotenv import load_dotenv
# Corrected: Using the modern 'ddgs' library directly instead of the langchain wrapper
from ddgs import DDGS

# Import services with fallbacks
try:
    from BizAgent.services.linkedin import run_pipeline as run_linkedin_pipeline
except ImportError:
    print("Warning: LinkedIn service not found.")
    def run_linkedin_pipeline(name, config=None): return "{'error': 'LinkedIn service not configured'}"
try:
    from BizAgent.reports.financial_report_tool import run_financial_report_pipeline
except ImportError:
    print("Warning: Financial Report service not found.")
    def run_financial_report_pipeline(name, config=None): return "Financial report service not configured."

# --- Environment and API Key Setup ---
load_dotenv()
os.environ.setdefault('SERPER_API_KEY', os.getenv('SERPER_API_KEY', ''))
SEC_API_KEY = os.getenv("SEC_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


# --- NEW: Smart Search Tool with Fallback ---
@tool("Smart Web Search")
def smart_search_tool(query: str, config: dict | None = None) -> str:
    """
    Performs a web search using DuckDuckGo as the primary engine.
    If it fails, it automatically falls back to using SerpAPI for the search.
    Use this for all general web search needs.
    """
    print(f"--- Performing smart search for: {query} ---")
    try:
        print("--- Trying DuckDuckGo Search (direct DDGS)... ---")
        with DDGS() as ddgs:
            # Using the modern ddgs library for more reliable results
            results = [r for r in ddgs.text(query, max_results=5)]
        
        if results:
            formatted_results = "\n\n".join(
                f"- Title: {r.get('title', 'N/A')}\n  URL: {r.get('href', 'N/A')}\n  Snippet: {r.get('body', 'N/A')}"
                for r in results
            )
            return f"### Search Results for '{query}':\n\n{formatted_results}"
        
        print("--- DuckDuckGo returned no results, falling back to SerpAPI. ---")
    except Exception as e:
        print(f"--- DuckDuckGo Search failed: {e}. Falling back to SerpAPI. ---")

    # Fallback to SerpAPI
    if not SERPAPI_KEY:
        return "Error: DuckDuckGo search failed and SERPAPI_KEY is not set for fallback."
    try:
        print("--- Trying SerpAPI Search... ---")
        from serpapi import GoogleSearch
        search = GoogleSearch({"q": query, "api_key": SERPAPI_KEY, "num": 5})
        results = search.get_dict().get("organic_results", [])
        if not results:
            return f"No search results found for: {query} from either search engine."
        return f"### Search Results for '{query}':\n\n" + "\n\n".join(
            f"- **Title:** {r.get('title', 'N/A')}\n  **Snippet:** {r.get('snippet', 'N/A')}"
            for r in results
        )
    except Exception as e:
        return f"An error occurred during the SerpAPI fallback search: {e}"

# --- Other Tool Definitions ---
@tool("Yahoo Finance Tool")
def yahoo_finance_tool(ticker: str, config: dict | None = None) -> str:
    """Fetches financial statements (Balance Sheet, Income Statement, Cash Flow) for a stock ticker from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        data = {
            "Balance Sheet": stock.balance_sheet.to_string(),
            "Income Statement": stock.income_stmt.to_string(),
            "Cash Flow": stock.cashflow.to_string()
        }
        if not any(val.strip() for val in data.values()):
            return f"Error: No financial data found for ticker '{ticker}'."
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching data from Yahoo Finance for '{ticker}': {e}"

@tool("Web URL Scraper")
def web_scraping_tool(url: str, config: dict | None = None) -> str:
    """Scrapes clean text content from a given website URL using Jina AI's reader API."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url, timeout=25)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error: Could not retrieve content from {url}: {e}"

@tool("PDF Content Extractor")
def fetch_pdf_content(pdf_path: str, config: dict | None = None) -> str:
    """Extracts all text content from a local PDF file given its file path."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PdfReader(f)
            text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e: return f"Error reading PDF {pdf_path}: {e}"

@tool("LinkedIn Company Insights Tool")
def linkedin_insights_tool(universal_name: str, config: dict | None = None) -> str:
    """Extracts, analyzes, and structures company insights from LinkedIn using a company's universal name (e.g., 'microsoft', 'google', 'monogram-health')."""
    if not universal_name:
        return "Error: A universal name for the LinkedIn company must be provided."
    print(f"--- Running LinkedIn pipeline for universal name: {universal_name} ---")
    return run_linkedin_pipeline(universal_name)

@tool("Financial Report Generator Tool")
def generate_financial_report_tool(company_name: str, config: dict | None = None) -> str:
    """Generates and returns the markdown content of a financial report."""
    try:
        return run_financial_report_pipeline(company_name)
    except Exception as e:
        return f"Error generating financial report for {company_name}: {e}"

@tool("EDGAR SEC Filings Fetcher")
def edgar_tool(ticker: str, config: dict | None = None) -> str:
    """Fetches key data from the latest 10-K SEC filing for a public company ticker."""
    if not SEC_API_KEY: return "Error: SEC_API_KEY not set."
    try:
        from sec_api import QueryApi, ExtractorApi
        filings = QueryApi(api_key=SEC_API_KEY).get_filings({"query": f"ticker:{ticker} AND formType:\"10-K\"", "from": "0", "size": "1", "sort": [{"filedAt": {"order": "desc"}}]})
        if not filings.get('filings'): return f"No 10-K filings for {ticker}"
        filing = filings['filings'][0]
        risk_factors = ExtractorApi(api_key=SEC_API_KEY).get_section(filing['linkToFilingDetails'], '1A', 'text')
        return f"### 10-K Summary: {filing.get('companyName')}\n- **Risks:** {risk_factors[:1000]}..."
    except Exception as e: return f"Error fetching SEC data: {e}"

@tool("Financial Modeling Prep Tool")
def fmp_tool(symbol: str, config: dict | None = None) -> str:
    """Fetches high-level financial data for a listed company via the FMP API."""
    if not FMP_API_KEY: return "Error: FMP_API_KEY not set."
    try:
        data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}").json()
        if not data: return f"No FMP data for {symbol}."
        d = data[0]
        return f"### Financial Profile: {d.get('companyName')}\n- **Price:** ${d.get('price')}\n- **Market Cap:** ${d.get('mktCap'):,}"
    except Exception as e: return f"Error with FMP tool: {e}"

@tool("Recent News Fetcher")
def news_tool(company_name: str, config: dict | None = None) -> str:
    """Fetches recent news articles for a given company name."""
    if not NEWSAPI_KEY: return "Error: NEWSAPI_KEY not set."
    try:
        from newsapi import NewsApiClient
        articles = NewsApiClient(api_key=NEWSAPI_KEY).get_everything(q=company_name, language="en", sort_by="publishedAt", page_size=5).get('articles', [])
        if not articles: return f"No recent news for {company_name}."
        return f"### Recent News for {company_name}:\n\n" + "\n\n".join(
            f"- **Title:** {a['title']}\n  **Summary:** {a.get('description', 'N/A')}"
            for a in articles
        )
    except Exception as e: return f"Error fetching news: {e}"

@tool("Wikipedia Company Scraper")
def wikipedia_company_tool(company_name: str, config: dict | None = None) -> str:
    """Extracts key company data from a Wikipedia infobox."""
    try:
        response = requests.get(f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}", headers={"User-Agent": "CrewAI-Agent/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        infobox = soup.find("table", {"class": "infobox vcard"})
        if not infobox: return f"No Wikipedia infobox for {company_name}."
        summary = f"### Wikipedia Profile: {company_name}:\n\n"
        for row in infobox.find_all("tr"):
            header, data = row.find("th"), row.find("td")
            if header and data:
                key = re.sub(r'\[\d+\]', '', header.get_text()).strip()
                value = re.sub(r'\[\d+\]', '', data.get_text(separator=', ', strip=True)).strip()
                if len(value) < 200: summary += f"- **{key}:** {value}\n"
        return summary
    except Exception as e: return f"Error fetching Wikipedia page: {e}"


#--------------------------------------------------------------------------------------------

# import json
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse, urljoin
# from tqdm import tqdm
# from crewai_tools import tool
# from langchain.tools import tool
# from PyPDF2 import PdfReader
# import re
# import google.generativeai as genai
# import os
# from crewai_tools import SerperDevTool
# from dotenv import load_dotenv
# from BizAgent.services.linkedin import run_pipeline
# load_dotenv()


# os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')

# @tool("Web url_scrapper")
# def web_scraping_tool(url: str) -> str:
#     """Scrapes data from a given website URL and returns the extracted text."""
    
#     def is_same_domain(base_url, new_url):
#         base_domain = urlparse(base_url).netloc
#         new_domain = urlparse(new_url).netloc
#         print(f"Checking domain: {new_domain} (Base: {base_domain})")
#         return base_domain == new_domain

#     def extract_text(html_content):
#         print("Extracting text from HTML content...")
#         soup = BeautifulSoup(html_content, 'html.parser')
#         for script_or_style in soup(['script', 'style']):
#             script_or_style.decompose()
#         text = soup.get_text(separator='\n')
#         lines = (line.strip() for line in text.splitlines())
#         text = '\n'.join(line for line in lines if line)
#         print("Text extraction complete.")
#         return text

#     def get_all_urls(base_url, max_depth=2):
#         print(f"Starting URL collection from {base_url} with max depth {max_depth}")
#         visited = set()
#         to_visit = [(base_url, 0)]
#         all_urls = set()

#         while to_visit:
#             current_url, depth = to_visit.pop(0)
#             print(f"Visiting {current_url} at depth {depth}")
#             parsed_url = urlparse(current_url)
#             current_url = current_url.replace(f'#{parsed_url.fragment}', '')

#             if current_url in visited or depth > max_depth:
#                 print(f"Skipping {current_url} (Already visited or depth exceeded)")
#                 continue

#             try:
#                 response = requests.get(current_url)
#                 response.raise_for_status()
#                 content = response.text
#                 visited.add(current_url)
#                 all_urls.add(current_url)
#                 print(f"Collected URL: {current_url}")

#                 if depth < max_depth:
#                     soup = BeautifulSoup(content, 'html.parser')
#                     links = soup.find_all('a', href=True)
#                     for link in links:
#                         new_url = urljoin(current_url, link['href'])
#                         if is_same_domain(base_url, new_url):
#                             new_url = new_url.replace(f'#{urlparse(new_url).fragment}', '')
#                             if new_url not in visited:
#                                 to_visit.append((new_url, depth + 1))
#             except Exception as e:
#                 print(f"Error while accessing {current_url}: {e}")

#         print("URL collection complete.")
#         return all_urls

#     def scrape_jina_ai(url):
#         print(f"Scraping content from Jina AI URL: {url}")
#         response = requests.get("https://r.jina.ai/" + url)
#         response.raise_for_status()
#         print(f"Scraping from {url} complete.")
#         return response.text

#     def scrape_url(url):
#         concatenated_content = ""
#         print("Starting URL scraping...")
#         try:
#             print(f"Scraping {url}...")
#             content = scrape_jina_ai(url)
#             text_content = extract_text(content)
#             concatenated_content += f"\n\n=== Content from {url} ===\n\n{text_content}"
#             print(f"Scraping and extraction for {url} complete.")
#         except Exception as e:
#             print(f"Error scraping {url}: {e}")
#             concatenated_content += f"\n\n=== Error scraping {url} ===\n\n{str(e)}"
#         print("URL scraping complete.")
#         return concatenated_content

#     return scrape_url(url)




# search_tool = SerperDevTool()




# @tool
# def fetch_pdf_content(pdf_url: str) -> str:
#     """
#     this tool converts pdf to text and returns it
#     Returns the content of the PDF.
#     """
#     # Open the local PDF file
#     with open(pdf_url, 'rb') as f:
#         pdf = PdfReader(f)
#         # Extract text from each page and join it into a single string
#         text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())

#     # Preprocess the extracted text to remove extra whitespace
#     processed_text = re.sub(r'\s+', ' ', text).strip()
    
#     # Return the processed text
    
#     return processed_text



# def fetch_text_content(text_url: str) -> str:
#     """

#     Reads and preprocesses content from a local text file.
#     Returns the text of the pdf as output.
    
#     """
#     # Open the local PDF file
#     with open(text_url, 'r', encoding='utf-8') as f:
#         doc = f.read()
 
#     return doc


# # tools.py
# @tool("LinkedIn Company Insights Tool")
# def linkedin_insights_tool(universal_name: str) -> str:
#     """Extract company insights and sales signals from LinkedIn (company profile + posts)."""
#     print("########### Running pipeline for:", universal_name)
#     insights = run_pipeline(universal_name)

#     # Ensure JSON string output
#     insights_json = json.dumps(insights, indent=2, ensure_ascii=False)

#     print("########### Insights returned:", insights_json[:200], "...")  # preview
#     return insights_json