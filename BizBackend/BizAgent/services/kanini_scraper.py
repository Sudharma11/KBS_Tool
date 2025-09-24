import os
import re
import time
import requests
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# --- LLM and Environment Setup ---
load_dotenv()
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

if not all([AZURE_OPENAI_KEY, AZURE_API_VERSION, AZURE_ENDPOINT, DEPLOYMENT_NAME]):
    raise ValueError("Missing one or more Azure OpenAI environment variables.")

llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    deployment_name=DEPLOYMENT_NAME,
    openai_api_version=AZURE_API_VERSION,
    temperature=0.2,
)

# --- Global variables for the crawler ---
session = requests.Session()

# -------- Helpers --------
def _normalize_base(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().lstrip("www.")

def _is_valid_url(url: str) -> bool:
    url = url.lower()
    skip_ext = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".avif", ".mp4", ".ico", ".pdf", ".pptx", ".docx")
    return not any(url.endswith(ext) for ext in skip_ext)

# -------- Enhanced Parsing Logic --------
def _extract_main_text(html: str) -> str:
    """
    More robustly extracts main content by checking semantic tags first,
    then common content containers, before falling back to the body.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    main_content_tags = soup.find_all(["main", "article", "section"])
    
    if not main_content_tags:
        main_content_tags = soup.find_all("div", id=re.compile(r'content|main|body', re.I))
        if not main_content_tags:
            main_content_tags = soup.find_all("div", class_=re.compile(r'content|main|body', re.I))

    if not main_content_tags:
        main_content_tags = [soup.body] if soup.body else []
    
    full_text = "\n\n".join([tag.get_text(separator="\n", strip=True) for tag in main_content_tags if tag])
    lines = [line.strip() for line in full_text.splitlines() if line.strip() and len(line.split()) > 2]

    return "\n".join(lines)

# -------- LLM Structuring Function --------
def _structure_scraped_content_with_llm(raw_text: str) -> str:
    """Uses a multi-stage LLM process to structure large amounts of raw text without a hard character limit."""
    if not raw_text.strip():
        return "No content was scraped from the website."

    print("--- Starting multi-stage structuring process... ---")
    chunk_size = 10000
    chunks = [raw_text[i:i + chunk_size] for i in range(0, len(raw_text), chunk_size)]
    
    intermediate_prompt = """You are a data extraction specialist. From the raw text provided below, extract and list all key points, facts, and details. Organize them under the following headings. Do not summarize, just extract the information:
- Offerings & Services
- Case Studies & Success Stories
- Accelerators & Proprietary Solutions
- Technologies & Platforms
- Industry Focus
- Company Mission & Values
- Other Key Information

**Raw Scraped Text Chunk:**
---
{chunk_text}
---
"""
    extracted_details = []
    for i, chunk in enumerate(chunks):
        print(f"--- Processing chunk {i+1}/{len(chunks)} for initial extraction... ---")
        try:
            prompt = intermediate_prompt.format(chunk_text=chunk)
            response = llm.invoke(prompt)
            extracted_details.append(response.content if hasattr(response, "content") else str(response))
            time.sleep(1) # Small delay to respect API rate limits
        except Exception as e:
            print(f"❌ Error processing chunk {i+1}: {e}")

    combined_extractions = "\n\n---\n\n".join(extracted_details)

    final_prompt = f"""You are an expert data analyst and report writer. Your task is to analyze the following collection of extracted data points from a company website and synthesize them into a single, well-structured, and comprehensive report. Your primary goal is to **organize all available information** into the specified categories. **Do not summarize or shorten the content**; present all the details you find in a clean, organized format.

The final output must be in markdown format and delineate the following sections:
- **Kanini Offerings & Core Services:** Detail all services mentioned.
- **Case Studies:** Describe any mentioned case studies or client success stories in detail.
- **Accelerators & IP:** Detail any proprietary accelerators, frameworks, or intellectual property.
- **Key Technologies & Platforms:** List all technologies and platforms mentioned.
- **Industry Focus:** List all industries the company serves.
- **Company Values & Mission:** Present the company's full mission and values.
- **Other Key Information & Insights:** Extract any other important details, partnerships, or noteworthy information.

Do not invent information. Use only the provided data.

**Combined Extracted Data:**
---
{combined_extractions}
---
"""
    try:
        print("--- Generating final structured report from combined data... ---")
        final_response = llm.invoke(final_prompt)
        return final_response.content if hasattr(final_response, "content") else str(final_response)
    except Exception as e:
        print(f"❌ LLM final synthesis failed: {e}")
        return f"Error: Could not synthesize the final report."

# -------- Main Crawler Function (Single-Pass, More Efficient) --------
def _fetch_and_parse(url: str, base_domain: str):
    """Fetches a single URL, scrapes its content, and finds new links."""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200 and "html" in resp.headers.get("Content-Type", ""):
            print(f"Successfully fetched {url}")
            html = resp.text
            text = _extract_main_text(html)
            
            soup = BeautifulSoup(html, "html.parser")
            links = [urljoin(url, a["href"]).split('#')[0] for a in soup.find_all("a", href=True)]
            valid_links = {link for link in links if _is_valid_url(link) and _normalize_base(link).endswith(base_domain)}
            return text, valid_links
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None, set()

def run_kanini_scrape_and_update(data_directory: str):
    base_url = "https://kanini.com/"
    workers = 10
    
    start_time = time.time()
    
    print("--- Starting Efficient Single-Pass Crawl... ---")
    
    queue = deque([base_url])
    visited = {base_url}
    all_content = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_fetch_and_parse, base_url, _normalize_base(base_url))}
        
        while futures:
            done, futures = as_completed(futures), set()
            
            for future in done:
                text, new_links = future.result()
                if text:
                    all_content.append(text)
                
                for link in new_links:
                    if link not in visited:
                        visited.add(link)
                        futures.add(executor.submit(_fetch_and_parse, link, _normalize_base(base_url)))

    print(f"✅ Crawling finished. Collected content from {len(all_content)} pages.")
    
    full_raw_text = "\n\n---\n\n".join(all_content)
    
    structured_output_path = os.path.join(data_directory, "KANINI_SERVICES.txt")
    raw_output_path = os.path.join(data_directory, "KANINI_SERVICES_raw.txt")
    
    try:
        os.makedirs(data_directory, exist_ok=True)
        with open(raw_output_path, "w", encoding="utf-8") as f:
            f.write(full_raw_text)
        print(f"✅ Raw scraped content saved to: {raw_output_path}")
    except Exception as e:
        print(f"❌ Error writing raw file: {e}")

    structured_content = _structure_scraped_content_with_llm(full_raw_text)
    try:
        with open(structured_output_path, "w", encoding="utf-8") as f:
            f.write(structured_content)
        print(f"✅ Structured content saved to: {structured_output_path}")
    except Exception as e:
        print(f"❌ Error writing structured file: {e}")

    end_time = time.time()
    print("✅ Scrape and structuring completed in {:.2f} seconds.".format(end_time - start_time))

