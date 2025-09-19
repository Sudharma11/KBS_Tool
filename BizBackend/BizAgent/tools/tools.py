import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from tqdm import tqdm
from crewai_tools import tool
from langchain.tools import tool
from PyPDF2 import PdfReader
import re
import google.generativeai as genai
import os
from crewai_tools import SerperDevTool
from BizAgent.reports.financial_report_tool import run_financial_report_pipeline
from dotenv import load_dotenv
load_dotenv()

os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')

@tool("Web url_scrapper")
def web_scraping_tool(url: str) -> str:
    """Scrapes data from a given website URL and returns the extracted text."""
    
    def is_same_domain(base_url, new_url):
        base_domain = urlparse(base_url).netloc
        new_domain = urlparse(new_url).netloc
        print(f"Checking domain: {new_domain} (Base: {base_domain})")
        return base_domain == new_domain

    def extract_text(html_content):
        print("Extracting text from HTML content...")
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        print("Text extraction complete.")
        return text

    def get_all_urls(base_url, max_depth=2):
        print(f"Starting URL collection from {base_url} with max depth {max_depth}")
        visited = set()
        to_visit = [(base_url, 0)]
        all_urls = set()

        while to_visit:
            current_url, depth = to_visit.pop(0)
            print(f"Visiting {current_url} at depth {depth}")
            parsed_url = urlparse(current_url)
            current_url = current_url.replace(f'#{parsed_url.fragment}', '')

            if current_url in visited or depth > max_depth:
                print(f"Skipping {current_url} (Already visited or depth exceeded)")
                continue

            try:
                response = requests.get(current_url)
                response.raise_for_status()
                content = response.text
                visited.add(current_url)
                all_urls.add(current_url)
                print(f"Collected URL: {current_url}")

                if depth < max_depth:
                    soup = BeautifulSoup(content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    for link in links:
                        new_url = urljoin(current_url, link['href'])
                        if is_same_domain(base_url, new_url):
                            new_url = new_url.replace(f'#{urlparse(new_url).fragment}', '')
                            if new_url not in visited:
                                to_visit.append((new_url, depth + 1))
            except Exception as e:
                print(f"Error while accessing {current_url}: {e}")

        print("URL collection complete.")
        return all_urls

    def scrape_jina_ai(url):
        print(f"Scraping content from Jina AI URL: {url}")
        response = requests.get("https://r.jina.ai/" + url)
        response.raise_for_status()
        print(f"Scraping from {url} complete.")
        return response.text

    def scrape_url(url):
        concatenated_content = ""
        print("Starting URL scraping...")
        try:
            print(f"Scraping {url}...")
            content = scrape_jina_ai(url)
            text_content = extract_text(content)
            concatenated_content += f"\n\n=== Content from {url} ===\n\n{text_content}"
            print(f"Scraping and extraction for {url} complete.")
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            concatenated_content += f"\n\n=== Error scraping {url} ===\n\n{str(e)}"
        print("URL scraping complete.")
        return concatenated_content

    return scrape_url(url)


search_tool = SerperDevTool()


@tool
def fetch_pdf_content(pdf_url: str) -> str:
    """
    this tool converts pdf to text and returns it
    Returns the content of the PDF.
    """
    # Open the local PDF file
    with open(pdf_url, 'rb') as f:
        pdf = PdfReader(f)
        # Extract text from each page and join it into a single string
        text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())

    # Preprocess the extracted text to remove extra whitespace
    processed_text = re.sub(r'\s+', ' ', text).strip()
    
    # Return the processed text
    
    return processed_text



def fetch_text_content(text_url: str) -> str:
    """

    Reads and preprocesses content from a local text file.
    Returns the text of the pdf as output.
    
    """
    # Open the local PDF file
    with open(text_url, 'r', encoding='utf-8') as f:
        doc = f.read()
 
    return doc

@tool("Generate Financial Report")
def generate_financial_report_tool(company_name: str) -> str:
    """Generates a markdown financial report for the given company using financial data."""
    return run_financial_report_pipeline(company_name)
