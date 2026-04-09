import requests
from bs4 import BeautifulSoup
import time
from googlesearch import search


def scrape_company_pages(company_name: str) -> str:
    """Scrape company website with comprehensive URL patterns."""

    company_slug = company_name.lower().replace(' ', '').replace('-', '')

    urls = [
        f"https://www.{company_slug}.com/leadership",
        f"https://www.{company_slug}.com/about/leadership",
        f"https://www.{company_slug}.com/company/leadership",
        f"https://www.{company_slug}.com/about-us/leadership",
        f"https://www.{company_slug}.com/who-we-are/leadership",
        f"https://{company_slug}.com/leadership",
        f"https://www.{company_slug}.com/team",
        f"https://www.{company_slug}.com/about/team",
        f"https://www.{company_slug}.com/our-team",
        f"https://www.{company_slug}.com/about",
        f"https://www.{company_slug}.com/about-us",
        f"https://www.{company_slug}.com/company",
        f"https://corporate.{company_slug}.com/leadership",
        f"https://investor.{company_slug}.com/leadership",
        f"https://investor.{company_slug}.com/governance/board-of-directors",
        f"https://investors.{company_slug}.com/corporate-governance/board-of-directors",
        f"https://www.{company_slug}.com/management",
        f"https://www.{company_slug}.com/executive-team",
        f"https://www.{company_slug}.com/executives",
        f"https://www.{company_slug}.com/en/about/leadership",
        f"https://www.{company_slug}.com/en-us/about/leadership",
        f"https://{company_slug}.com/en/leadership",
    ]

    all_text = ""
    for url in urls:
        try:
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator=' ', strip=True)
                if len(text) > 500:
                    all_text += text[:15000] + "\n\n"
                    print(f"  Scraped: {url[:60]} ({len(text)} chars)")
        except:
            continue

    if len(all_text) < 5000:
        print(f"  Low data, searching Google for {company_name} leadership page...")
        try:
            time.sleep(2)
            query = f'"{company_name}" leadership team executives'
            results = list(search(query, num_results=5, sleep_interval=2))

            for url in results[:3]:
                try:
                    response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        for tag in soup(["script", "style", "nav", "footer"]):
                            tag.decompose()
                        text = soup.get_text(separator=' ', strip=True)
                        if len(text) > 500:
                            all_text += text[:15000] + "\n\n"
                            print(f"  Scraped (Google): {url[:60]} ({len(text)} chars)")
                except:
                    continue
        except:
            pass

    return all_text[:30000]
