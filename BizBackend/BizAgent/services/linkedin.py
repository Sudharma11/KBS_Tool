import os
import json
import requests
import logging
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# ----------------------------
# Config
# ----------------------------
load_dotenv()
LINKEDIN_KEY = os.getenv("LINKEDIN_KEY")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

if not all([LINKEDIN_KEY, AZURE_OPENAI_KEY, AZURE_ENDPOINT, DEPLOYMENT_NAME]):
    raise ValueError("Missing one or more Azure/OpenAI/LinkedIn environment variables.")

HEADERS = {"X-API-Key": LINKEDIN_KEY}
BASE_URL = "https://api.harvest-api.com/linkedin"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# LLM init (Azure OpenAI)
llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    deployment_name=DEPLOYMENT_NAME,
    openai_api_version=AZURE_API_VERSION,
    temperature=0.2,
)

# --------------------------------------------------------
# API Helpers & Data Processing
# --------------------------------------------------------
def _safe_request(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"API request failed: {url} | {e}")
        return {}

def _get_company(universal_name: str) -> dict:
    data = _safe_request(f"{BASE_URL}/company?universalName={universal_name}")
    return data.get("element", {})

def _get_company_posts(universal_name: str, max_pages: int = 1) -> list:
    posts = []
    for page in range(1, max_pages + 1):
        data = _safe_request(f"{BASE_URL}/company-posts?companyUniversalName={universal_name}&page={page}")
        posts.extend(data.get("elements", []))
    return posts

# ----------------------------
# LLM-Powered Analysis Functions
# ----------------------------
def _summarize_with_llm(prompt: str) -> str:
    try:
        resp = llm.invoke(prompt)
        return resp.content.strip()
    except Exception as e:
        logging.error(f"LLM invocation failed: {e}")
        return f"Error: Could not generate summary due to an LLM error: {e}"

def _analyze_company_profile(company_info: dict) -> str:
    if not company_info:
        return "No company profile data was provided."
    
    profile_for_analysis = {
        "name": company_info.get("name"),
        "description": company_info.get("description"),
        "industries": company_info.get("industries"),
        "specialities": company_info.get("specialities"),
        "employeeCount": company_info.get("employeeCount"),
        "headquarter": company_info.get("headquarter"),
    }

    prompt = f"""
You are a Senior Business Analyst. Based on the following LinkedIn company profile data, write a concise summary that covers the company's core business, size, and key focus areas.

Company Data:
{json.dumps(profile_for_analysis, indent=2)}
"""
    return _summarize_with_llm(prompt)

def _analyze_company_posts(posts: list) -> str:
    if not posts:
        return "No recent post activity found on LinkedIn."
    
    all_post_content = "\n\n---\n\n".join(
        [post.get('content', '') for post in posts if post.get('content')]
    )
    if not all_post_content.strip():
        return "Recent posts contained no readable text content."

    prompt = f"""
You are a strategic analyst. Based on the following collection of recent LinkedIn posts from a company, identify and summarize the key themes. Focus on:
1.  **Strategic Priorities:** What are they consistently talking about (e.g., product launches, hiring, events, technology trends)?
2.  **Company Culture & Tone:** What is the overall tone of their communications?
3.  **Potential Business Signals:** Are there any hints of expansion, new partnerships, or challenges they are trying to solve?

LinkedIn Posts:
{all_post_content[:8000]}
"""
    return _summarize_with_llm(prompt)

# ----------------------------
# Main Pipeline - Corrected to break the loop
# ----------------------------
def run_pipeline(universal_name: str) -> str:
    """
    Main pipeline to fetch, analyze, and structure LinkedIn data.
    Returns a single, structured markdown string.
    """
    logging.info(f"--- Starting LinkedIn Pipeline for: {universal_name} ---")
    
    company_info = _get_company(universal_name)
    if not company_info:
        error_msg = f"Failed to retrieve company data for '{universal_name}'. The universal name may be incorrect or the API key may be invalid."
        logging.error(error_msg)
        return f"### LinkedIn Analysis Error\n\n{error_msg}"

    company_posts = _get_company_posts(universal_name, max_pages=1)

    company_summary = _analyze_company_profile(company_info)
    posts_summary = _analyze_company_posts(company_posts)
    
    # This now builds the final report string directly
    final_report = f"""
### LinkedIn Profile Summary
{company_summary}

### Key Insights from Recent Activity
{posts_summary}
"""
    
    logging.info("--- LinkedIn Pipeline Completed Successfully ---")
    return final_report

