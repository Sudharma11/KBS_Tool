import logging
import json
import random
import time
import concurrent.futures
from typing import Dict, List
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, GoogleSerperAPIWrapper
import google.generativeai as genai
from urllib.parse import urlparse
import re
import warnings
from bs4 import XMLParsedAsHTMLWarning
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from Levenshtein import distance as levenshtein
from app.core.prompts import SITEMAP_ANALYST, CSUITE_SITE_FILTER_PROMPT, HTML_PARSING_KEYS
from app.core.config import GEMINI_API_KEYS, SERPER_API_KEY
import os

os.environ.setdefault("SERPER_API_KEY", SERPER_API_KEY)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger().setLevel(logging.ERROR)

class IgnoreNoiseFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage().lower()
        blocked_patterns = [
            "valueerror('not enough values to unpack",
            "not enough values to unpack (expected 2, got 1)",
            "error in engine",
            "duckduckgo search failed",
            "serper search failed",
        ]
        return not any(pattern in msg for pattern in blocked_patterns)

logging.getLogger().addFilter(IgnoreNoiseFilter())
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BROWSER_AI_OVERVIEW_PROMPT = """
You are an AI search assistant analyzing web search results to identify company executives and leadership teams - similar to an "AI Overview" feature.

**COMPANY:** {company_name}

**SEARCH RESULTS TO ANALYZE:**
{search_results}

**YOUR TASK:**
Analyze ALL the search results above and extract a comprehensive list of executives and leaders for {company_name}. Act like an AI Overview that synthesizes information from multiple sources.

**APPROACH:**
1. Look for executive names, titles, and roles across ALL search results
2. Synthesize information from multiple sources to build a complete picture
3. Resolve conflicts or inconsistencies between sources
4. Include all C-suite executives, VPs, Presidents, and senior leaders
5. Focus on current executives (not former or historical)

**SPECIFIC ROLES TO LOOK FOR:**
- CEO, Chief Executive Officer, President
- CFO, Chief Financial Officer  
- CTO, Chief Technology Officer
- COO, Chief Operating Officer
- Chief Medical Officer
- Chief Strategy Officer
- Chief Growth Officer
- Chief Commercial Officer
- Chief Delivery Officer
- Chief Solutions Officer
- Chief Transformation Officer
- Executive Vice President
- Senior Vice President
- Vice President
- SVP - Healthcare Business Unit Leader
- Chief Program Management Officer
- Operating Officer & Chief Financial Officer

**EXTRACTION RULES:**
- Extract names and roles even if they're mentioned in different sources
- Combine information from multiple sources about the same person
- Prefer more specific role titles over generic ones
- Include LinkedIn profiles when mentioned
- Include source URLs so we know where each piece of information came from

**OUTPUT FORMAT:**
Return a JSON array of executive objects. Each object should contain:
- Name: Full name of the executive
- Role: Their official title/role
- LinkedinURL: LinkedIn profile URL if found (null if not)
- source_url: The URL where this information was found
- confidence: Your confidence in this information (0.0-1.0)

**EXAMPLE:**
```json
[
  {{
    "Name": "John Smith",
    "Role": "Chief Executive Officer",
    "LinkedinURL": "https://linkedin.com/in/johnsmith",
    "source_url": "https://company.com/leadership",
    "confidence": 0.95
  }},
  {{
    "Name": "Jane Doe", 
    "Role": "Chief Financial Officer",
    "LinkedinURL": null,
    "source_url": "https://news.com/article",
    "confidence": 0.85
  }}
]
"""
TARGETED_AI_ANALYSIS_PROMPT = """
You are analyzing targeted search results for specific executive roles at a company.

**COMPANY:** {company_name}

**SEARCH STRATEGY:**
We conducted targeted searches for each specific executive role. Below are the search results organized by the role we were searching for.

**SEARCH RESULTS:**
{search_results}

**YOUR MISSION:**
Extract specific executives that match our target roles. We searched for each role specifically, so focus on finding the actual people in these positions.

**TARGET ROLES WE SEARCHED FOR:**
{target_roles_list}

**EXTRACTION RULES:**
1. Only extract executives that match our target roles
2. If a search result is for a specific role (like "CTO Blue Cross NC"), extract that executive
3. Look for name-role pairs in titles and snippets
4. Include LinkedIn profiles when available
5. Be precise - only include executives that clearly match our target roles

**OUTPUT FORMAT:**
```json
[
  {{
    "Name": "Executive Name",
    "Role": "Specific Target Role", 
    "LinkedinURL": "linkedin_url_or_null",
    "source_url": "url_where_found",
    "confidence": 0.0-1.0,
    "searched_role": "which_target_role_we_searched_for"
  }}
]
BE PRECISE AND TARGETED - ONLY EXTRACT EXECUTIVES THAT MATCH OUR SPECIFIC ROLE SEARCHES.
"""

TARGET_ROLES = {
'svp - healthcare business unit leader',
'chief delivery officer',
'president/ceo',
'chief commercial officer',
'chief solutions officer',
'chief transformation officer',
'chief strategy and growth officer',
'executive vice president',
'chief technology officer',
'chief program management officer',
'operating officer & chief financial officer',
'chief executive officer',
'chief financial officer',
'chief operating officer',
'chief technology officer',
'chief strategy officer',
'chief growth officer',
'chief commercial officer',
'chief delivery officer'
}

def duckduckgo_search(query: str,n : int) -> List[Dict]:
    try:
        wrapper = DuckDuckGoSearchAPIWrapper(region="uk")
        search = DuckDuckGoSearchResults(api_wrapper=wrapper, output_format="list", num_results=n)
        return search.invoke(query)
    except Exception as e:
        logger.error(f"DuckDuckGo search failed for {query}: {str(e)}")
        raise RuntimeError(f"DuckDuckGo search failed: {e}")



def get_response_json_match(text: str) -> str:
    try:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        return match.group(1) if match else text
    except Exception as e:
        raise RuntimeError(f"Error extracting JSON: {e}")


def load_json(text: str) -> Dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def get_response_text(response: genai.types.GenerateContentResponse) -> str:
    try:
        if response and response.candidates:
          
            return response.text
        raise ValueError("No response text available")
    except Exception as e:
        raise RuntimeError(f"Error extracting response text: {e}")


def serper_search(query: str,n : int) -> List[Dict]:
    try:
        serper = GoogleSerperAPIWrapper(k=n, type="search")
        results = serper.results(query)
        return results.get('organic', [])
    except Exception as e:
        raise RuntimeError(f"Serper search failed: {e}")

def get_robots_url(url: str):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            raise ValueError("Invalid URL: no domain found")
        
        if not url.startswith(f"https://{domain}/"):
            if not url.endswith("/"):
                url += "/"
            else:
                raise ValueError("Invalid URL format")
        
        robots_url = f"https://{domain}/robots.txt"
        return robots_url, f"https://{domain}/"
    except Exception as e:
        raise ValueError(f"Failed to process URL: {str(e)}")

def scrape_data(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
       
        content_type = resp.headers.get('content-type', '').lower()
        is_xml = '.xml' in url.lower() or 'xml' in content_type or resp.text.strip().startswith('<?xml')
        
        if is_xml:
           
            try:
                soup = BeautifulSoup(resp.text, 'xml')  
            except Exception:
              
                try:
                    soup = BeautifulSoup(resp.text, 'lxml-xml')
                except Exception:
                    soup = BeautifulSoup(resp.text, 'html.parser')  
        else:
         
            soup = BeautifulSoup(resp.text, "html.parser")
        
        metadata = {
            "title": soup.title.string if soup.title else None,
            "description": None,
            "keywords": None,
            "favicon": None
        }
        
       
        if not is_xml:
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag:
                metadata["description"] = desc_tag.get("content")
            
            keywords_tag = soup.find("meta", attrs={"name": "keywords"})
            if keywords_tag:
                metadata["keywords"] = keywords_tag.get("content")
            
            icon_tag = soup.find("link", rel=lambda v: v and "icon" in v.lower())
            if icon_tag:
                metadata["favicon"] = urljoin(url, icon_tag.get("href"))
        
        return metadata, soup
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch URL {url}: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error scraping data from {url}: {str(e)}")

def extract_sitemap(text: str):
    try:
        urls = re.findall(r'(?i)\b(?:altlang\s+)?sitemap:\s*(https?://\S+)', text)
        if not urls:
            raise ValueError("No sitemap URLs found")
        return urls
    except Exception as e:
        raise ValueError(f"Error extracting sitemap: {str(e)}")

def extract_sitemap_urls(text: str, base_tokens: List[str] = ["sitemap", "altlang"]):
    try:
        text = text.lower()
        lines = text.splitlines()
        anagram_hashes = {''.join(sorted(t)) for t in base_tokens}
        sitemap_urls = []
        
        for line in lines:
            words = re.findall(r"[a-zA-Z\-]+", line)
            if any(
                ''.join(sorted(w)) in anagram_hashes or 
                any(levenshtein(w, t) <= 2 for t in base_tokens)
                for w in words
            ):
                urls = re.findall(r"http?://[^\s]+", line)
                for u in urls:
                    if urlparse(u).scheme in ["http", "https"]:
                        sitemap_urls.append(u)
        
        if not sitemap_urls:
            sitemap_urls = extract_sitemap(text)
        
        if not sitemap_urls:
            raise ValueError("No valid sitemap URLs found")
        
        return sitemap_urls
    except Exception as e:
        raise ValueError(f"Error extracting sitemap URLs: {str(e)}")

def extract_xml_urls(text: str):
    try:
        pattern = r"https?://[^\s]+?\.xml"
        urls = re.findall(pattern, text)
        if not urls:
            raise ValueError("No XML URLs found")
        return urls
    except Exception as e:
        raise ValueError(f"Error extracting XML URLs: {str(e)}")

def get_sitemap_list(sitemap_xmls: List[str]):
    try:
        if not sitemap_xmls:
            raise ValueError("Sitemap list is empty")
        return sitemap_xmls
    except Exception as e:
        raise ValueError(f"Error processing sitemap list: {str(e)}")

def sitemap_rerank_ai(company_name: str, sitemaps_list: str) -> genai.types.GenerateContentResponse:
    try:
        genai.configure(api_key=random.choice(GEMINI_API_KEYS))
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            contents=[SITEMAP_ANALYST.format(company_name=company_name), sitemaps_list]
        )
        return response 
    except Exception as e:
        raise RuntimeError(f"Error in sitemap reranking: {str(e)}")

def extract_site_urls(text: str):
    try:
        url_pattern = r"https?://[^\s]+"
        all_urls = re.findall(url_pattern, text)
        
        file_extensions = (
            r"\.(png|jpg|jpeg|gif|bmp|svg|webp|ico|pdf|docx?|xlsx?|pptx?|zip|rar|mp4|mp3|mov|avi|txt|csv|json|xml)$"
        )
        
        site_urls = [url for url in all_urls if not re.search(file_extensions, url, re.IGNORECASE)]
        
        if not site_urls:
            raise ValueError("No valid site URLs found")
        
        return site_urls
    except Exception as e:
        raise ValueError(f"Error extracting site URLs: {str(e)}")

def get_sitemap_data(pages_url: List[str], j: int):
    try:
        if not pages_url:
            raise ValueError("Pages URL list is empty")
        
        site_urls = []
        pages_str = ""
        for idx, i in enumerate(pages_url, j):
            site_urls.append({"id": idx + 1, "url": i})
            pages_str += f"Id: {idx + 1} | URL: {i}\n"
        
        return pages_str, site_urls, idx
    except Exception as e:
        raise ValueError(f"Error processing sitemap data: {str(e)}")

def filter_lead_sites_ai(pages_str: str):
    try:
        genai.configure(api_key=random.choice(GEMINI_API_KEYS))
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            contents=[CSUITE_SITE_FILTER_PROMPT, pages_str]
        )
        response_text = get_response_text(response)
        if not response_text:
            raise ValueError("No response text from AI")
        return response_text
    except Exception as e:
        raise RuntimeError(f"Error in filtering lead sites: {str(e)}")

def url_optimization_pipeline(url, company_name):
    try:
        robots_url, _ = get_robots_url(url)
        _, soup = scrape_data(robots_url)

        sitemap_xmls = extract_xml_urls(soup.text)
        _, soup = scrape_data(sitemap_xmls[0])

        sitemap_list = get_sitemap_list(soup.text)
        sitemap_response = sitemap_rerank_ai(company_name, sitemap_list)
        
        
        response_extracted = get_response_json_match(sitemap_response)
        response_json = load_json(response_extracted)
        response_json = [primary for primary in response_json if primary.get("isPrimary", False) == True]

        sitemap_scraped = []
        sitemap_str = ""
        j = 0
        for idx, sitemap in enumerate(response_json):
            _, soup = scrape_data(sitemap['url'])
            time.sleep(2)  
            site_urls = extract_site_urls(soup.text)
            pages_str, site_urls, j = get_sitemap_data(site_urls, j)
            sitemap_str += pages_str
            sitemap_scraped.append(site_urls)

        response = filter_lead_sites_ai(pages_str)
        response_text = get_response_text(response) 
        response_extracted = get_response_json_match(response_text)
        response_json = load_json(response_extracted)
        return response_json
    except Exception as e:
        logger.warning(f"URL optimization pipeline failed: {e}")
        raise e
    
def extract_json_from_text(text: str) -> str:
    """Extract JSON from text with multiple fallback methods"""
 
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    
    return text.strip()

def parse_json_safely(json_text: str) -> List[Dict]:
    """Safely parse JSON with multiple attempts"""
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning(f"First JSON parse failed: {e}, trying to fix common issues")
        
      
        fixed_json = fix_common_json_issues(json_text)
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError as e2:
            logger.error(f"Fixed JSON also failed: {e2}")
            return []
        
def fix_common_json_issues(json_text: str) -> str:
    """Fix common JSON formatting issues"""
    # Remove trailing commas
    fixed = re.sub(r',\s*}', '}', json_text)
    fixed = re.sub(r',\s*]', ']', fixed)
    
    # Ensure proper quotes
    fixed = re.sub(r'(\w+):', r'"\1":', fixed)
    
    # Fix missing quotes around keys
    fixed = re.sub(r'{\s*(\w+)\s*:', r'{"\1":', fixed)
    
    return fixed
def ensure_unique_profiles(profiles):
    """
    Ensure all profiles have unique names (case-insensitive)
    Returns list of profiles with duplicates removed
    """
    logger = logging.getLogger(__name__)
    
    if not profiles:
        return []
    
    unique_profiles = []
    seen_names = set('joseph bastante')
    duplicates_removed = 0
    
    for profile in profiles:
        profile_name = profile.get('Name', '').strip()
        
        if not profile_name:
            continue
            
        normalized_name = normalize_name(profile_name)
        
        if normalized_name not in seen_names:
            unique_profiles.append(profile)
            seen_names.add(normalized_name)
        else:
            duplicates_removed += 1
            logger.debug(f"Removed duplicate: {profile_name}")
    
    logger.info(f"Removed {duplicates_removed} duplicate profiles, kept {len(unique_profiles)} unique profiles")
    return unique_profiles

def normalize_name(name):
    """Normalize name for comparison"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r'\b(Dr|Mr|Ms|Mrs|Jr|Sr|II|III)\b\.?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip().lower()


def extract_clean_body(soup):
    logger.debug("Cleaning body HTML: removing <script> and <style> tags")
    if soup is None:
        logger.warning("extract_clean_body received None soup")
        return ""
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()
    for tag in soup.find_all(True):
        attrs_to_keep = ['src', 'href']
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep or 'link' in k}
    return str(soup)

def remove_html_comments(html):
    logger.debug("Removing HTML comments")
    html = html.replace("<div>", "").replace("</div>", "")
    return re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

def remove_empty_tags(html):
    logger.debug("Removing empty tags")
    return re.sub(r'<(\w+)([^>]*)>\s*</\1>', '', html)

def strip_spaces(data):
    logger.debug("Stripping blank lines and extra spaces")
    return "\n".join([line for line in data.split("\n") if line.strip() != ""])

def remove_navs_and_comments_bs(html: str) -> str:
    logger.debug("Removing nav, link, input, head, and form elements")
    soup = BeautifulSoup(html, "html.parser")
    for tag_name in ["nav", "link", "input", "head", "form"]:
        for nav in soup.find_all(tag_name):
            nav.decompose()
    return str(soup)

def ner_csuite_profiles_ai(content):
    logger.info("Calling Gemini API for NER extraction")
    try:
        genai.configure(api_key=random.choice(GEMINI_API_KEYS))
    
        model = genai.GenerativeModel('gemini-2.0-flash') #gemini-2.5-flash-lite-preview-06-17
        response = model.generate_content(
            contents=[HTML_PARSING_KEYS, content]  
        )
        logger.debug("Received response from Gemini API")
        return response
    except Exception as e:
        logger.exception(f"Gemini API call failed: {e}")
        return {}
    
def browser_style_ai_search(company_name: str, company_url: str = None) -> List[Dict]:
    """
    Search specifically for each target role
    """
    logger.info(f"Starting targeted role search for: {company_name}")
    
    leaders_from_pages = []
    
    # If company_url is provided, use url_optimization_pipeline to get leadership pages
    if company_url:
        try:
            logger.info(f"Using URL optimization pipeline for: {company_url}")
            leadership_pages = url_optimization_pipeline(company_url, company_name)
            logger.info(f"Found {len(leadership_pages)} leadership pages from sitemap analysis")
            
            # Scrape each leadership page to extract person data
            for page in leadership_pages:
                try:
                    page_url = page.get('url')
                    if page_url:
                        logger.info(f"Scraping leadership page: {page_url}")
                        metadata, soup = scrape_data(page_url)
                        
                       
                        soup_body = extract_clean_body(soup)
                        soup_body_no_comments = remove_html_comments(soup_body)
                        soup_body_cleaned = remove_empty_tags(soup_body_no_comments)
                        cleaned = remove_navs_and_comments_bs(strip_spaces(soup_body_cleaned))
                        
                  
                        response = ner_csuite_profiles_ai(cleaned)
                        response_text = get_response_text(response)
                        response_match = get_response_json_match(response_text)
                        response_json = load_json(response_match)
                    
                        for profile in response_json:
                            profile['source_url'] = page_url
                            profile['source_type'] = 'sitemap_analysis'
                        
                        leaders_from_pages.extend(response_json)
                        logger.info(f"Extracted {len(response_json)} profiles from {page_url}")
                        
                        time.sleep(2)  
                        
                except Exception as e:
                    logger.warning(f"Failed to scrape leadership page {page.get('url')}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"URL optimization pipeline failed: {e}. Moving to search-based approach.")
  
    browser_queries = []
    
    
    for role in TARGET_ROLES:
        
        clean_role = role.replace('/', ' ').replace('&', 'and')
        
       
        query_variations = [
            f"{clean_role} {company_name}",
            f"{company_name} {clean_role}",
            f'"{clean_role}" "{company_name}"'
        ]
    
        for query in query_variations:
            if query not in browser_queries:
                browser_queries.append(query)
    
    all_search_data = []
  
    for i, query in enumerate(browser_queries, 1):
        try:
            results = duckduckgo_search(query, 3)  
            
            for result in results:
                result_data = {
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'search_query': query,
                    'target_role': extract_role_from_query(query, company_name)
                }
                all_search_data.append(result_data)
                
        except Exception as e:
            try:
              
                results = serper_search(query, 3)
                
                for result in results:
                    result_data = {
                        'title': result.get('title', ''),
                        'url': result.get('link', ''),
                        'snippet': result.get('snippet', ''),
                        'search_query': query,
                        'target_role': extract_role_from_query(query, company_name)
                    }
                    all_search_data.append(result_data)
            except Exception as e2:
                logger.info(f"Serper search failed for: {company_name}")
    
    leaders_from_search = ai_overview_analysis(all_search_data, company_name)
    print(leaders_from_pages)
    # Combine leaders from sitemap analysis and search
    all_leaders = leaders_from_pages + leaders_from_search
    
    logger.info(f"Total leaders found: {len(leaders_from_pages)} from sitemap + {len(leaders_from_search)} from search = {len(all_leaders)} total")
    
    return all_leaders

def extract_role_from_query(query: str, company_name: str) -> str:
    """Extract the target role from search query"""

    clean_query = query.replace(company_name, '').strip()
    
   
    for role in TARGET_ROLES:
        role_clean = role.replace('/', ' ').replace('&', 'and')
        if (role in clean_query or 
            role_clean in clean_query or
            get_role_abbreviation(role) in clean_query):
            return role
    
    return "General Search"

def get_role_abbreviation(role: str) -> str:
    """Get abbreviation for role"""
    abbr_map = {
        'chief executive officer': 'CEO',
        'chief financial officer': 'CFO',
        'chief operating officer': 'COO', 
        'chief technology officer': 'CTO',
        'chief strategy officer': 'CSO',
        'chief growth officer': 'CGO',
        'chief commercial officer': 'CCO',
        'chief delivery officer': 'CDO',
        'executive vice president': 'EVP',
        'svp - healthcare business unit leader': 'SVP',
        'president/ceo': 'President CEO'
    }
    return abbr_map.get(role.lower(), role.split()[0].upper() if ' ' in role else role.upper())

def _slug_matches_name(url: str, name: str) -> bool:
    """Check if the LinkedIn profile slug contains at least one word from the person's name."""
    try:
        path = urlparse(url).path  # e.g. /in/john-smith-abc123
        slug = path.strip('/').split('/')[-1].lower()  # john-smith-abc123
        slug_tokens = set(re.split(r'[-_]', slug))
        name_tokens = {w.lower() for w in name.split() if len(w) > 1}
        return bool(name_tokens & slug_tokens)
    except Exception:
        return False


def enrich_linkedin(responses, company_name):
    logger = logging.getLogger(__name__)
    logger.info(f"Enriching {len(responses)} profiles with LinkedIn URLs")
    wrapper = DuckDuckGoSearchAPIWrapper(region="uk", max_results=3)
    search = DuckDuckGoSearchResults(api_wrapper=wrapper, output_format="list")
    serper = GoogleSerperAPIWrapper(k=3, type="search")

    def search_linkedin(response):
        try:
            name = response.get('Name', '')
            if response.get("LinkedinURL") and _slug_matches_name(response["LinkedinURL"], name):
                logger.debug(f"Valid LinkedIn URL already present for {name}")
                return response

            query = f'"{name}" "{company_name}" site:linkedin.com/in'

            # Try DuckDuckGo first
            try:
                results = search.invoke(query)
            except Exception:
                results = []

            # Validate each result — slug must match the person's name
            for result in results:
                url = result.get('link', '')
                parsed = urlparse(url)
                if parsed.netloc in ['linkedin.com', 'www.linkedin.com'] and '/in/' in parsed.path:
                    if _slug_matches_name(url, name):
                        response['LinkedinURL'] = url
                        logger.info(f"DDG LinkedIn match for {name}: {url}")
                        return response

            # Fallback to Serper
            try:
                serper_results = serper.results(query)
                for result in serper_results.get('organic', []):
                    url = result.get('link', '')
                    parsed = urlparse(url)
                    if parsed.netloc in ['linkedin.com', 'www.linkedin.com'] and '/in/' in parsed.path:
                        if _slug_matches_name(url, name):
                            response['LinkedinURL'] = url
                            logger.info(f"Serper LinkedIn match for {name}: {url}")
                            return response
            except Exception:
                pass

            response['LinkedinURL'] = None
            logger.info(f"No valid LinkedIn match found for {name}")
            return response
        except Exception as e:
            logger.exception(f"LinkedIn enrichment failed for {response.get('Name')}: {e}")
            return response

    enriched = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(search_linkedin, resp) for resp in responses]
        for future in concurrent.futures.as_completed(futures):
            enriched.append(future.result())
    return enriched

def ai_overview_analysis(search_data: List[Dict], company_name: str) -> List[Dict]:
    """AI analyzes targeted search results"""
    logger.info("Starting targeted AI analysis of search results")


    formatted_results = ""
    role_groups = {}

    for result in search_data:
        role = result.get('target_role', 'General')
        if role not in role_groups:
            role_groups[role] = []
        role_groups[role].append(result)

   
    for role, results in role_groups.items():
        formatted_results += f"\n🔍 SEARCHED FOR: {role}\n"
        formatted_results += f"📊 Found {len(results)} results:\n"
        
        for i, result in enumerate(results[:5], 1): 
            formatted_results += f"""
                                RESULT {i}:
                                Title: {result['title']}
                                URL: {result['url']}
                                Snippet: {result['snippet']}

                                """

    
    target_roles_list = "\n".join([f"- {role}" for role in sorted(TARGET_ROLES)])

    try:
        genai.configure(api_key=random.choice(GEMINI_API_KEYS))
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = model.generate_content(
            contents=[TARGETED_AI_ANALYSIS_PROMPT.format(
                company_name=company_name,
                search_results=formatted_results,
                target_roles_list=target_roles_list
            )]
        )
        
        text = get_response_text(response)
        
        
        extracted = extract_json_from_text(text)
        leaders = parse_json_safely(extracted)
        
        if not isinstance(leaders, list):
           
            return fallback_leader_extraction(search_data, company_name)
        
       
        return leaders
        
    except Exception as e:
       
        return fallback_leader_extraction(search_data, company_name)


def process_browser_style_search(company_name: str, company_url: str = None) -> List[Dict]:
    """Main function — uses NameScraper pipeline (scrape → LLM extract → verify)."""
    from app.leader_extraction.extractor import extract_leaders
    return extract_leaders(company_name)

def fallback_leader_extraction(search_data: List[Dict], company_name: str) -> List[Dict]:
    """
    Fallback method to extract leaders when AI fails
    """
    
    leaders = []
    seen_names = set()
    
  
    executive_patterns = [
        r'\b(?:President|CEO|Chief Executive Officer)\b.*?([A-Z][a-z]+ [A-Z][a-z]+)',
        r'\b(CFO|Chief Financial Officer)\b.*?([A-Z][a-z]+ [A-Z][a-z]+)',
        r'\b(CTO|Chief Technology Officer)\b.*?([A-Z][a-z]+ [A-Z][a-z]+)',
        r'\b(COO|Chief Operating Officer)\b.*?([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+).*?\b(?:President|CEO|Chief|Officer|VP|Vice President)\b',
    ]
    
    for result in search_data:
        text = f"{result['title']} {result['snippet']}".lower()
  
        if any(indicator in text for indicator in [
            'ceo', 'cfo', 'cto', 'coo', 'chief', 'president', 
            'executive', 'officer', 'vice president', 'vp'
        ]):
   
            for pattern in executive_patterns:
                matches = re.findall(pattern, f"{result['title']} {result['snippet']}", re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:
                            role, name = match
                        else:
                           
                            name, role = extract_name_role_from_text(f"{result['title']} {result['snippet']}")
                    else:
                        name, role = extract_name_role_from_text(f"{result['title']} {result['snippet']}")
                    
                  
                    if role and isinstance(role, str):
                        role_clean = role.strip()
                    else:
                        role_clean = 'Executive'
                    
                    if name and isinstance(name, str) and name not in seen_names:
                        name_clean = name.strip()
                        seen_names.add(name_clean)
                        leaders.append({
                            'Name': name_clean,
                            'Role': role_clean,
                            'source_url': result['url'],
                            'confidence': 0.7,
                            'source': 'fallback_extraction'
                        })
    
    logger.info(f"Fallback extraction found {len(leaders)} leaders")
    return leaders

def extract_name_role_from_text(text: str) -> tuple:
    """Extract name and role from text using simple patterns"""
    
    patterns = [
        r'([A-Z][a-z]+ [A-Z][a-z]+).*?(President|CEO|Chief|Officer|VP)',
        r'(President|CEO|Chief|Officer|VP).*?([A-Z][a-z]+ [A-Z][a-z]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return groups[1], groups[0] if groups[0].istitle() else (groups[1], groups[0])
    
    return None, None


if __name__ == "__main__":
    leaders = process_browser_style_search(
        company_name="Blue Cross NC", 
        company_url="https://www.bluecrossnc.com"
    )
    print(leaders)