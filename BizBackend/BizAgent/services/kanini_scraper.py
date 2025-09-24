import os
import re
import time
import requests
from collections import deque, Counter
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# --- LLM and Environment Setup ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing Google API key in .env file")

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",
#     temperature=0.2,
#     google_api_key=GOOGLE_API_KEY,
# )
from langchain_openai import AzureChatOpenAI

# --- LLM and Environment Setup ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing Google API key in .env file")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
)

# LLM init (Azure OpenAI)
llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    deployment_name=DEPLOYMENT_NAME,
    openai_api_version=AZURE_API_VERSION,
    temperature=0.2,
)
# --- Global variables for the crawler ---
session = requests.Session()
global_line_counter = Counter()

# -------- Helpers --------
def _normalize_base(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().lstrip("www.")

def _is_valid_url(url: str) -> bool:
    url = url.lower()
    skip_ext = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".avif", ".mp4", ".ico", ".pdf", ".pptx", ".docx")
    return not any(url.endswith(ext) for ext in skip_ext)

# -------- Parsing Logic --------
def _extract_main_text(html: str, record_lines=False) -> str:
    """Extract main content dynamically, removing headers/footers."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    candidates = soup.find_all(["div", "article", "section", "main"])
    main_content = max(candidates, key=lambda t: len(t.get_text(strip=True)), default=soup)

    lines = [line.strip() for line in main_content.get_text(separator="\n", strip=True).splitlines() if line.strip()]
    cleaned_lines = [line for line in lines if len(line.split()) > 2]

    if record_lines:
        global_line_counter.update(cleaned_lines)

    return "\n".join(cleaned_lines)

def _remove_boilerplate(text: str, min_repeats=5) -> str:
    """Remove lines that repeat across many pages (headers/footers)."""
    lines = text.splitlines()
    return "\n".join([l for l in lines if global_line_counter[l] < min_repeats])

# -------- LLM Structuring Function --------
def _structure_scraped_content_with_llm(raw_text: str) -> str:
    """Uses an LLM to structure the raw scraped text into a professional summary."""
    if not raw_text.strip():
        return "No content was scraped from the website."

    text_for_analysis = raw_text[:12000]

    prompt = f"""
You are a Senior Business Analyst and Content Strategist. Your task is to analyze the following raw, unstructured text scraped from the Kanini company website and transform it into a well-structured, detailed report. Your goal is to organize *all* the information into the specified categories without summarizing or losing any details.

The final output should be in markdown format and must clearly delineate the following sections:
- **Kanini Offerings & Core Services:** Extract and detail all services Kanini offers (e.g., Application Development, AI & Analytics, Cloud Services).
- **Case Studies:** Detail any mentioned case studies or client success stories.
- **Accelerators & IP:** Detail any proprietary accelerators, frameworks, or intellectual property mentioned.
- **Key Technologies & Platforms:** List all primary technologies, platforms, and frameworks mentioned (e.g., AWS, Azure, Python, .NET).
- **Industry Focus:** List all key industries Kanini serves (e.g., Healthcare, BFSI, Manufacturing).
- **Company Values & Mission:** Extract and present the company's mission statement, values, or overall business philosophy in detail.
- **Other Key Information & Insights:** Extract any other important details, partnerships, or noteworthy information that does not fit into the above categories.

Do not invent or summarize information. Extract and present all relevant details for each section based *only* on the provided text.

**Raw Scraped Text:**
---
{text_for_analysis}
---
"""
    try:
        print("--- Structuring scraped content with LLM... ---")
        response = llm.invoke(prompt)
        structured_content = response.content if hasattr(response, "content") else str(response)
        print("--- Content structuring complete. ---")
        return structured_content
    except Exception as e:
        print(f"❌ LLM structuring failed: {e}")
        return f"Error: Could not structure the scraped content. Raw content: \n\n{raw_text}"

# -------- Main Crawler Function --------
def _process_url(url: str, base_domain: str, record_lines: bool = False):
    """Processes a single URL, returns its text content and any new links found."""
    try:
        resp = session.get(url, timeout=15)
        ctype = resp.headers.get("Content-Type", "").lower()
        print(f"[{url}] -> Status {resp.status_code}, Type {ctype}")

        if resp.status_code == 200 and "html" in ctype:
            html_content = resp.text
            text_content = _extract_main_text(html_content, record_lines=record_lines)
            
            soup = BeautifulSoup(html_content, "html.parser")
            links = []
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"]).split('#')[0]
                if _is_valid_url(full_url) and _normalize_base(full_url).endswith(base_domain):
                    links.append(full_url)
            return text_content, links
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None, []

def run_kanini_scrape_and_update(output_file_path: str):
    base_url = "https://kanini.com/"
    max_depth = 3
    workers = 8
    
    base_domain = _normalize_base(base_url)
    visited = set()
    all_content = []
    
    start_time = time.time()
    
    # --- Pass 1: Crawl sequentially to build boilerplate counter ---
    print("--- Starting Pass 1: Identifying boilerplate content... ---")
    queue = deque([(base_url, 0)])
    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)
        
        _, new_links = _process_url(url, base_domain, record_lines=True)
        for link in new_links:
            if link not in visited:
                queue.append((link, depth + 1))

    # --- Pass 2: Crawl in parallel and clean the text ---
    print("\n--- Starting Pass 2: Scraping and cleaning content... ---")
    visited.clear()
    queue = deque([(base_url, 0)])
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        while queue:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            futures.append(executor.submit(_process_url, url, base_domain, record_lines=False))
        
        for future in as_completed(futures):
            text, new_links = future.result() if future.result() is not None else (None, [])
            if text:
                cleaned_text = _remove_boilerplate(text)
                all_content.append(cleaned_text)
            for link in new_links:
                if link not in visited:
                    queue.append((link, depth + 1))

    print(f"✅ Crawling finished. Visited {len(visited)} URLs.")
    
    full_raw_text = "\n\n---\n\n".join(all_content)
    
    # --- Final Step: Structure the content using the LLM ---
    structured_content = _structure_scraped_content_with_llm(full_raw_text)

    try:
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(structured_content)
        print(f"✅ KANINI_SERVICES.txt has been updated with structured content at {output_file_path}")
    except Exception as e:
        print(f"❌ Error writing to file {output_file_path}: {e}")

    end_time = time.time()
    print("✅ Scrape and structuring completed in {:.2f} seconds.".format(end_time - start_time))

