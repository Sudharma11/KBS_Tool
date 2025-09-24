import os
import json
import requests
import logging
from dotenv import load_dotenv
from collections import defaultdict
from langchain_openai import AzureChatOpenAI
import tiktoken

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
    raise ValueError("Missing one or more Azure/OpenAI/LinkedIn environment variables in .env")

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
# API Helpers
# --------------------------------------------------------
def safe_request(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"API request failed: {url} | {e}")
        return {}

def get_company(universal_name: str) -> dict:
    data = safe_request(f"{BASE_URL}/company?universalName={universal_name}")
    return data.get("element", {})

def get_company_posts(universal_name: str, max_pages: int = 2) -> list:
    posts = []
    for page in range(1, max_pages + 1):
        data = safe_request(f"{BASE_URL}/company-posts?companyUniversalName={universal_name}&page={page}")
        posts.extend(data.get("elements", []))
    return posts

# ----------------------------
# Processing & Summarization
# ----------------------------
def summarize_text_with_llm(prompt: str, max_tokens: int = 15000) -> str:
    """Invokes the LLM to summarize provided text based on a prompt."""
    if len(prompt) > max_tokens * 3:
         logging.warning("Prompt might be too long, truncating.")
         prompt = prompt[:max_tokens * 3]
    try:
        resp = llm.invoke(prompt)
        return resp.content.strip()
    except Exception as e:
        logging.error(f"LLM invocation failed: {e}")
        return "Error: Could not generate summary."


def summarize_company_info(company_info: dict) -> str:
    prompt = f"""
You are a Senior Business Analyst. Review the following company information from LinkedIn and extract key insights. 
Focus on summarizing their mission, size, specialities, and any potential risks or weaknesses evident from the data.

Company Data:
{json.dumps(company_info, indent=2)}
"""
    return summarize_text_with_llm(prompt)

def summarize_posts(posts: list) -> str:
    """Summarizes a list of posts into key themes."""
    if not posts:
        return "No recent post activity found."
    
    all_post_content = "\n\n---\n\n".join([post.get('content', '') for post in posts])
    
    prompt = f"""
You are a business analyst. I will provide you with recent LinkedIn posts from a company. 
Analyze these posts and summarize the key themes, focusing on:
1.  **Strategic Priorities:** What are they focused on (e.g., product launches, hiring, events)?
2.  **Market Position & Branding:** How do they present themselves to the public?
3.  **Potential Business Opportunities:** Are there any signals for potential partnerships or sales?

LinkedIn Posts:
{all_post_content}
"""
    return summarize_text_with_llm(prompt)

# ----------------------------
# Main Pipeline
# ----------------------------
def run_pipeline(universal_name: str) -> dict:
    """
    Main pipeline to fetch company info and posts, then generate summaries.
    Returns a dictionary of insights.
    """
    logging.info(f"--- Starting LinkedIn Pipeline for: {universal_name} ---")
    
    company_info = get_company(universal_name)
    if not company_info:
        logging.error("Could not fetch company info. Aborting pipeline.")
        return {"error": f"Failed to retrieve company data for {universal_name}."}

    company_posts = get_company_posts(universal_name, max_pages=1)

    logging.info("🔹 Summarizing company profile...")
    company_summary = summarize_company_info(company_info)
    
    logging.info("🔹 Summarizing recent posts...")
    posts_summary = summarize_posts(company_posts)
    
    insights = {
        "company_summary": company_summary,
        "posts_summary": posts_summary,
    }
    
    logging.info("--- LinkedIn Pipeline Completed Successfully ---")
    return insights

