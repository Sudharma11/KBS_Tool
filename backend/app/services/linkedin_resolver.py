import logging
import time
import re
from urllib.parse import urlparse
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
import requests
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

import os
os.environ['DUCKDUCKGO_SEARCH_NO_WARNINGS'] = '1'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def find_linkedin_company_url(company_data):
    """
    Find LinkedIn company URL with strict validation to avoid subsidiary pages and unwanted paths
    """
    logger = logging.getLogger(__name__)
    company_name = company_data.get("company_name")
    website = company_data.get("website", "")
    
    if not company_name:
        return {"error": "Company name is required"}
    
    logger.info(f"Searching for main LinkedIn URL for: {company_name}")
    
    try:
        ddg_wrapper = DuckDuckGoSearchAPIWrapper(region="us-en", max_results=10)
        ddg_search = DuckDuckGoSearchResults(api_wrapper=ddg_wrapper, output_format="list", response_format="content_and_artifact")
        
        # Clean company name for exact matching
        clean_name = re.sub(r'[^\w\s]', '', company_name).strip().lower()
        
        # More targeted queries to find the main company page
        search_queries = [
            # Direct searches for official page
            f'"{company_name}" official LinkedIn company page',
            f'"{company_name}" LinkedIn company official',
            f'site:linkedin.com/company "{company_name}" official',
            f'"{company_name}" LinkedIn main company page',
            # Generic but with more results to filter
            f'site:linkedin.com/company "{company_name}"',
            f'"{company_name}" LinkedIn company',
        ]
        
        all_candidates = []
        
        for query in search_queries:
            try:
                logger.debug(f"Searching: {query}")
                results = ddg_search.invoke(query)
                
                for result in results:
                    if 'link' in result:
                        url = result['link']
                        title = result.get('title', '').lower()
                        
                        # Clean the URL to remove unwanted paths
                        clean_url = clean_linkedin_url(url)
                        
                        if is_main_company_linkedin_url(clean_url, company_name, title):
                            score = calculate_main_company_score(clean_url, company_name, title, result.get('snippet', ''))
                            
                            candidate = {
                                'url': clean_url,
                                'score': score,
                                'title': title,
                                'query': query,
                                'snippet': result.get('snippet', ''),
                                'original_url': url  # Keep original for reference
                            }
                            all_candidates.append(candidate)
                            logger.debug(f"Valid main company candidate: {clean_url} (score: {score})")
                
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"Query failed: {query} - {e}")
                continue
        
        # Filter and select the best candidate
        best_candidate = select_main_company_candidate(all_candidates, company_name)
        
        if best_candidate:
            return {
                "resolved_url": best_candidate['url'],
                "confidence": best_candidate['confidence'],
                "method": "main_company_search",
                "company_name": company_name,
                "matched_query": best_candidate.get('query', ''),
                "score": best_candidate['score']
            }
        
        return {
            "resolved_url": None,
            "error": "No main company LinkedIn URL found",
            "company_name": company_name
        }
            
    except Exception as e:
        logger.exception(f"LinkedIn search failed for {company_name}: {e}")
        return {"error": f"Search failed: {str(e)}"}

def clean_linkedin_url(url):
    """
    Remove unwanted paths from LinkedIn URLs like /jobs, /about, /people, etc.
    Returns only the main company page URL
    """
    try:
        parsed_url = urlparse(url)
        
        # List of unwanted paths to remove
        unwanted_paths = [
            '/jobs', '/job', '/careers', '/career',
            '/about', '/people', '/life', '/products',
            '/services', '/insights', '/news', '/events',
            '/learning', '/showcase', '/admin', '/edit',
            '/analytics', '/sales', '/marketing'
        ]
        
        # Split the path and keep only the base company path
        path_parts = parsed_url.path.split('/')
        
        # We want: /company/company-name only
        if len(path_parts) >= 3 and path_parts[1] == 'company':
            # Take only the first three parts: /company/company-name
            clean_path = '/'.join(path_parts[:3])
            
            # Reconstruct the URL with only the clean path
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{clean_path}"
            return clean_url
        
        return url  # Return original if we can't parse it properly
        
    except Exception as e:
        logger.debug(f"URL cleaning failed for {url}: {e}")
        return url

def is_main_company_linkedin_url(url, company_name, title=""):
    """
    Strict validation to ensure this is the main company page, not a subsidiary
    """
    try:
        parsed_url = urlparse(url)
        
        # Must be LinkedIn company URL
        if not (parsed_url.netloc in ['linkedin.com', 'www.linkedin.com'] and '/company/' in parsed_url.path):
            return False
        
        # Extract company slug and check path length
        path_parts = parsed_url.path.split('/')
        if len(path_parts) < 3:
            return False
        
        # After cleaning, path should be exactly 3 parts: /company/company-name
        if len(path_parts) > 3:
            return False
        
        company_slug = path_parts[2].lower()
        clean_company_name = company_name.lower()
        
        # Common subsidiary indicators to exclude
        subsidiary_indicators = [
            '-careers', '-jobs', '-recruitment', '-talent', '-hr',
            '-engineering', '-technology', '-tech', '-solutions',
            '-services', '-consulting', '-consultants',
            '-india', '-us', '-uk', '-europe', '-asia', '-americas',
            '-division', '-unit', '-group', '-holdings',
            '-infrastructure', '-digital', '-innovation', '-ventures',
            'career', 'recruitment', 'talent', 'jobs'
        ]
        
        # Check if URL contains subsidiary indicators
        for indicator in subsidiary_indicators:
            if indicator in company_slug:
                logger.debug(f"Rejected subsidiary URL: {url} (indicator: {indicator})")
                return False
        
        # Check title for main company indicators
        title_lower = title.lower()
        main_company_indicators = [
            'official', 'main', 'company', 'corporate', 'global',
            'home', 'welcome', f"{clean_company_name} company"
        ]
        
        # If title suggests it's the main page, give it a chance
        title_score = 0
        for indicator in main_company_indicators:
            if indicator in title_lower:
                title_score += 1
        
        # Basic name matching
        clean_name_simple = re.sub(r'[^a-z0-9]', '', clean_company_name)
        if clean_name_simple in company_slug:
            return True
        
        # Check for partial matches of main company name
        words = clean_company_name.split()
        if len(words) > 0 and words[0] in company_slug:
            return True
            
        return title_score >= 2  # Require strong title indicators if name doesn't match exactly
        
    except Exception as e:
        logger.debug(f"URL validation failed: {e}")
        return False

def calculate_main_company_score(url, company_name, title="", snippet=""):
    """
    Calculate score for main company page likelihood
    """
    score = 0
    
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        company_slug = path_parts[2].lower() if len(path_parts) > 2 else ""
        clean_company_name = company_name.lower()
        clean_name_simple = re.sub(r'[^a-z0-9]', '', clean_company_name)
        
        # Exact name match is best
        if company_slug == clean_name_simple:
            score += 20
        
        # Close matches
        if clean_name_simple in company_slug:
            score += 15
        
        # Simple slug (no extra words) is better
        if '-' not in company_slug or company_slug.count('-') <= 1:
            score += 10
        
        # Title indicators
        title_lower = title.lower()
        if 'official' in title_lower:
            score += 8
        if 'company' in title_lower and 'linkedin' in title_lower:
            score += 5
        if clean_company_name in title_lower:
            score += 5
        
        # Snippet indicators
        snippet_lower = snippet.lower()
        if 'official' in snippet_lower:
            score += 3
        if 'main' in snippet_lower:
            score += 3
        if 'company page' in snippet_lower:
            score += 3
            
        # Penalize complex slugs (likely subsidiaries)
        if company_slug.count('-') >= 2:
            score -= 5
        
        # Bonus for clean URL (no extra paths)
        if len(path_parts) == 3:
            score += 5
            
    except Exception as e:
        logger.debug(f"Scoring failed: {e}")
    
    return max(0, score)

def select_main_company_candidate(candidates, company_name):
    """
    Select the best main company candidate
    """
    if not candidates:
        return None
    
    # Sort by score descending
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Get top candidates
    top_candidates = candidates[:3]
    
    # If we have a clear winner with high score, use it
    if top_candidates[0]['score'] >= 15:
        best = top_candidates[0]
        confidence = "high" if best['score'] >= 20 else "medium"
        best['confidence'] = confidence
        return best
    
    # Otherwise, try to find the simplest URL (most likely main page)
    simplest_candidate = None
    for candidate in top_candidates:
        slug = urlparse(candidate['url']).path.split('/')[2]
        if simplest_candidate is None or len(slug) < len(simplest_candidate):
            simplest_candidate = candidate
    
    if simplest_candidate and simplest_candidate['score'] >= 10:
        simplest_candidate['confidence'] = "medium"
        return simplest_candidate
    
    return None

# Enhanced version with URL cleaning as first step
def find_linkedin_company_url_with_cleaning(company_data):
    """
    Find LinkedIn URL with aggressive URL cleaning to remove unwanted paths
    """
    logger = logging.getLogger(__name__)
    
    # First try the main company search
    result = find_linkedin_company_url(company_data)
    
    # If we found something, ensure it's cleaned
    if result.get('resolved_url'):
        cleaned_url = clean_linkedin_url(result['resolved_url'])
        result['resolved_url'] = cleaned_url
        result['method'] = result.get('method', '') + '_cleaned'
        
        # Verify the cleaned URL
        if not verify_cleaned_url(cleaned_url, company_data['company_name']):
            # If verification fails, try alternative approach
            alternative_result = find_linkedin_direct(company_data)
            if alternative_result.get('resolved_url'):
                return alternative_result
    
    return result

def verify_cleaned_url(url, company_name):
    """
    Verify that the cleaned URL is valid and makes sense
    """
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        
        # Should be exactly 3 parts: /company/company-name
        if len(path_parts) != 3:
            return False
        
        # Company slug should not be empty
        company_slug = path_parts[2]
        if not company_slug:
            return False
        
        # Basic name relevance check
        clean_name = re.sub(r'[^\w\s]', '', company_name).lower()
        clean_slug = company_slug.lower().replace('-', ' ')
        
        return any(word in clean_slug for word in clean_name.split()[:2])
        
    except:
        return False

def find_linkedin_direct(company_data):
    """
    Direct approach: construct the most obvious URL and verify it
    """
    company_name = company_data['company_name']
    
    # Create clean slug from company name
    clean_slug = re.sub(r'[^\w\s]', '', company_name).strip().lower().replace(' ', '-')
    direct_url = f"https://www.linkedin.com/company/{clean_slug}"
    
    # Verify this URL by searching for it
    ddg_wrapper = DuckDuckGoSearchAPIWrapper(region="us-en", max_results=3)
    ddg_search = DuckDuckGoSearchResults(api_wrapper=ddg_wrapper, output_format="list", response_format="content_and_artifact")
    
    try:
        results = ddg_search.invoke(f'"{direct_url}"')
        if results and any('link' in result for result in results):
            return {
                "resolved_url": direct_url,
                "confidence": "medium",
                "method": "direct_construction",
                "company_name": company_name
            }
    except:
        pass
    
    return {"resolved_url": None, "error": "Direct construction failed"}

# Final robust function
def find_linkedin_company_url_final(company_data):
    """
    Final robust function with multiple layers of URL cleaning and validation
    """
    logger = logging.getLogger(__name__)
    company_name = company_data.get("company_name")
    
    logger.info(f"Final LinkedIn search for: {company_name}")
    
    # Try the enhanced cleaning approach first
    result = find_linkedin_company_url_with_cleaning(company_data)
    
    # If still no result, try direct construction
    if not result.get('resolved_url'):
        direct_result = find_linkedin_direct(company_data)
        if direct_result.get('resolved_url'):
            return direct_result
    
    return result

# Usage example
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        {
            "company_name": "Blue Cross NC",
            "website": "https://www.bluecrossnc.com/"
        }
    ]
    
    for test_data in test_cases:
        print(f"\n{'='*50}")
        print(f"Searching for: {test_data['company_name']}")
        
        result = find_linkedin_company_url_final(test_data)
        print(f"Final result: {result}")
     