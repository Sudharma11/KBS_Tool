import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
import json
from typing import Dict, List, Optional

class WebsiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_company_website(self, url: str) -> str:
        """Main method to scrape company website and return text output"""
        try:
            print(f"Scraping website: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            company_data = {
                "basic_info": self._extract_basic_info(soup, url),
                "contact_info": self._extract_contact_info(soup, url),
                "products_services": self._extract_products_services(soup, url),
                "about_section": self._extract_about_section(soup, url),
                "key_pages": self._extract_key_pages(soup, url),
                "social_links": self._extract_social_links(soup),
                "technologies": self._detect_technologies(soup, response)
            }
            
            return self._format_as_text(company_data)
            
        except Exception as e:
            return f"Error scraping website {url}: {str(e)}"
    
    def _extract_basic_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract basic company information"""
        basic_info = {}
        
        basic_info['company_name'] = self._extract_company_name(soup)
        basic_info['website_url'] = url
        basic_info['title'] = self._extract_title(soup)
        basic_info['meta_description'] = self._extract_meta_description(soup)
        basic_info['logo'] = self._extract_logo(soup, url)
        
        return basic_info
    
    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """Extract company name from various sources"""
        # Try title first
        title = soup.find('title')
        if title:
            name = title.get_text().strip()
            # Remove common suffixes
            name = re.sub(r'[\-\|:].*$', '', name).strip()
            if name and len(name) < 100:
                return name
        
        # Try h1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text().strip()
            if text and len(text) < 100 and len(text) > 3:
                return text
        
        # Try meta company name
        meta_company = soup.find('meta', attrs={'name': 'company'})
        if meta_company and meta_company.get('content'):
            return meta_company.get('content')
        
        # Try og:site_name
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return og_site.get('content')
        
        return "Unknown Company"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content')
        
        return ""
    
    def _extract_logo(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract company logo"""
        logo_selectors = [
            '.logo', '#logo', '.header-logo', '.site-logo', '.navbar-logo',
            'img[alt*="logo"]', 'img[alt*="Logo"]', 'img[alt*="brand"]',
            'img[src*="logo"]', 'img[class*="logo"]',
            '.custom-logo', '.site-branding img'
        ]
        
        for selector in logo_selectors:
            logo_imgs = soup.select(selector)
            for logo_img in logo_imgs:
                if logo_img and logo_img.get('src'):
                    logo_src = logo_img['src']
                    if logo_src.startswith('http'):
                        return logo_src
                    else:
                        return urljoin(base_url, logo_src)
        
        # Try og:image as fallback
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image.get('content')
        
        return ""
    
    def _extract_contact_info(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Extract contact information with improved methods"""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'contact_page_url': ''
        }
        
        # First, try to find contact page
        contact_url = self._find_contact_page(soup, base_url)
        if contact_url:
            contact_info['contact_page_url'] = contact_url
            # Try to extract from contact page
            try:
                contact_response = self.session.get(contact_url, timeout=5)
                if contact_response.status_code == 200:
                    contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                    # Extract from contact page
                    contact_info['emails'].extend(self._extract_emails_from_soup(contact_soup))
                    contact_info['phones'].extend(self._extract_phones_from_soup(contact_soup))
                    contact_info['addresses'].extend(self._extract_addresses_from_soup(contact_soup))
            except:
                pass
        
        # Also extract from main page
        contact_info['emails'].extend(self._extract_emails_from_soup(soup))
        contact_info['phones'].extend(self._extract_phones_from_soup(soup))
        contact_info['addresses'].extend(self._extract_addresses_from_soup(soup))
        
        # Remove duplicates and clean data
        contact_info['emails'] = list(set(contact_info['emails']))[:5]
        contact_info['phones'] = list(set(contact_info['phones']))[:5]
        contact_info['addresses'] = list(set(contact_info['addresses']))[:3]
        
        return contact_info
    
    def _find_contact_page(self, soup: BeautifulSoup, base_url: str) -> str:
        """Find contact page URL"""
        contact_keywords = ['contact', 'contact-us', 'get-in-touch', 'reach-us']
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            
            if any(keyword in href or keyword in text for keyword in contact_keywords):
                full_url = urljoin(base_url, link['href'])
                # Skip javascript links and anchors
                if not (full_url.startswith('javascript:') or full_url.startswith('#')):
                    return full_url
        return ""
    
    def _extract_emails_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Extract emails from BeautifulSoup object"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text_content = soup.get_text()
        emails = re.findall(email_pattern, text_content)
        
        # Filter out common false positives
        filtered_emails = []
        for email in emails:
            # Skip example emails and common false positives
            if not any(domain in email.lower() for domain in ['example.com', 'domain.com', 'email.com']):
                filtered_emails.append(email)
        
        return filtered_emails
    
    def _extract_phones_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Extract phone numbers from BeautifulSoup object"""
        phone_patterns = [
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{1,14}'
        ]
        
        phones = []
        text_content = soup.get_text()
        
        for pattern in phone_patterns:
            found_phones = re.findall(pattern, text_content)
            for phone in found_phones:
                if isinstance(phone, tuple):
                    phone = ''.join(phone)
                # Clean and validate phone number
                clean_phone = re.sub(r'[^\d+]', '', phone)
                if 7 <= len(clean_phone) <= 15:
                    phones.append(phone.strip())
        
        return phones
    
    def _extract_addresses_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Extract addresses from BeautifulSoup object"""
        # Look for address in specific elements
        address_elements = soup.find_all(['address', '[class*="address"]', '[id*="address"]'])
        addresses = []
        
        for elem in address_elements:
            text = elem.get_text().strip()
            if len(text) > 10 and len(text) < 200:
                # Basic validation - should contain numbers and street words
                if re.search(r'\d+', text) and any(word in text.lower() for word in 
                                                  ['street', 'st', 'avenue', 'ave', 'road', 'rd', 
                                                   'lane', 'ln', 'boulevard', 'blvd', 'drive', 'dr']):
                    addresses.append(' '.join(text.split()))
        
        return addresses

    def _extract_products_services(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract real products and services information"""
        products_services = []
        
        # Look for actual service/offering sections, not just navigation
        service_keywords = [
            'consulting', 'technology', 'operations', 'strategy', 'digital',
            'cloud', 'security', 'ai', 'analytics', 'transformation'
        ]
        
        # Method 1: Look for service/offering sections in main content
        content_selectors = [
            '[data-testid*="service"]', '[class*="service"]', '[class*="offering"]',
            '[class*="solution"]', '[class*="capability"]', '.services-list',
            '.offerings-grid', '.solutions-section'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Get headings within service sections
                headings = element.find_all(['h2', 'h3', 'h4', 'h5'])
                for heading in headings:
                    text = heading.get_text().strip()
                    if text and 5 < len(text) < 100:
                        products_services.append(text)
        
        # Method 2: Look for specific service pages in navigation
        nav_links = soup.find_all('a', href=True)
        service_links_found = set()
        
        for link in nav_links:
            href = link['href'].lower()
            text = link.get_text().strip()
            
            # Look for service-related links with meaningful text
            if (any(keyword in href for keyword in ['service', 'solution', 'offering', 'capability']) or
                any(keyword in text.lower() for keyword in service_keywords)):
                
                if text and len(text) > 3 and len(text) < 80:
                    full_url = urljoin(base_url, link['href'])
                    service_links_found.add((text, full_url))
        
        # Add service links as products/services
        for text, url in list(service_links_found)[:10]:
            products_services.append(f"{text}")
        
        # Method 3: Look for industry solutions
        industry_keywords = ['industry', 'sector', 'vertical']
        for link in nav_links:
            href = link['href'].lower()
            text = link.get_text().strip()
            
            if any(keyword in href for keyword in industry_keywords):
                if text and len(text) > 3 and len(text) < 80:
                    products_services.append(f"{text} Solutions")
        
        # Clean and filter results
        cleaned_products = []
        seen = set()
        
        for item in products_services:
            # Clean the text
            clean_item = ' '.join(item.split())
            # Filter out navigation items, menu items, and non-service content
            if (clean_item and 
                len(clean_item) > 5 and 
                len(clean_item) < 100 and
                clean_item not in seen and
                not any(word in clean_item.lower() for word in ['menu', 'search', 'login', 'sign', 'home', 'contact'])):
                
                seen.add(clean_item)
                cleaned_products.append(clean_item)
        
        return cleaned_products[:15]
    
    def _extract_about_section(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Extract about us information with proper links"""
        about_info = {
            "about_texts": [],
            "mission": "",
            "vision": "", 
            "leadership": [],
            "history": "",
            "values": [],
            "about_links": []  # Store actual about page links
        }
        
        # Find all about-related links
        about_links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().strip().lower()
            href = link['href'].lower()
            
            about_keywords = ['about', 'company', 'story', 'mission', 'vision', 'values', 'leadership', 'history', 'culture']
            
            if any(keyword in link_text or keyword in href for keyword in about_keywords):
                full_url = urljoin(base_url, link['href'])
                # Skip javascript links, anchors, and main page
                if (not full_url.startswith('javascript:') and 
                    not full_url.startswith('#') and
                    full_url != base_url.rstrip('/')):
                    
                    about_links.append({
                        'title': link.get_text().strip(),
                        'url': full_url
                    })
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in about_links:
            if link['url'] not in seen_urls and len(link['title']) > 2:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        about_info['about_links'] = unique_links[:10]
        
        # Try to extract content from the main about page if available
        main_about_url = None
        for link in about_links:
            if 'about' in link['url'].lower():
                main_about_url = link['url']
                break
        
        if main_about_url:
            try:
                about_response = self.session.get(main_about_url, timeout=8)
                if about_response.status_code == 200:
                    about_soup = BeautifulSoup(about_response.content, 'html.parser')
                    
                    # Extract main content
                    content_selectors = [
                        'main', '.content', '#content', '.about-content', 
                        '.page-content', '[class*="about"]', 'article'
                    ]
                    
                    for selector in content_selectors:
                        content_elems = about_soup.select(selector)
                        for elem in content_elems:
                            text = elem.get_text().strip()
                            if len(text) > 200:
                                # Clean the text
                                clean_text = ' '.join(text.split())
                                about_info['about_texts'].append(clean_text[:800])
                    
                    # Look for mission/vision specifically
                    for tag in about_soup.find_all(['p', 'div', 'section']):
                        text = tag.get_text().lower()
                        if 'mission' in text and len(tag.get_text().strip()) > 30:
                            about_info['mission'] = ' '.join(tag.get_text().strip().split())[:400]
                        elif 'vision' in text and len(tag.get_text().strip()) > 30:
                            about_info['vision'] = ' '.join(tag.get_text().strip().split())[:400]
                            
            except Exception as e:
                print(f"Could not fetch about page {main_about_url}: {e}")
        
        # If no about pages were fetched, try to extract from current page
        if not about_info['about_texts']:
            about_sections = soup.select('[class*="about"], section, main, article')
            for section in about_sections:
                text = section.get_text().strip()
                if len(text) > 150:
                    clean_text = ' '.join(text.split())
                    about_info['about_texts'].append(clean_text[:500])
        
        return about_info
    
    def _extract_key_pages(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract important page links"""
        key_pages = []
        important_keywords = [
            'about', 'contact', 'product', 'service', 'solution', 
            'pricing', 'blog', 'news', 'career', 'team', 'portfolio',
            'case study', 'whitepaper', 'resource', 'download'
        ]
        
        links = soup.find_all('a', href=True)
        seen_urls = set()
        
        for link in links:
            href = link['href']
            text = link.get_text().strip()
            
            if not text or len(text) < 2:
                continue
                
            full_url = urljoin(base_url, href)
            
            # Skip if already seen or if it's the same as base URL or javascript links
            if (full_url in seen_urls or full_url == base_url.rstrip('/') or
                full_url.startswith('javascript:') or full_url.startswith('#')):
                continue
                
            # Check if link is important
            link_text_lower = text.lower()
            href_lower = href.lower()
            
            if (any(keyword in link_text_lower or keyword in href_lower 
                   for keyword in important_keywords) and
                len(text) < 100):  # Reasonable link text length
                
                key_pages.append({
                    'title': text,
                    'url': full_url
                })
                seen_urls.add(full_url)
        
        # Remove duplicates by URL and limit results
        unique_pages = []
        seen_titles = set()
        for page in key_pages:
            if page['title'] not in seen_titles:
                unique_pages.append(page)
                seen_titles.add(page['title'])
        
        return unique_pages[:15]
    
    def _extract_social_links(self, soup: BeautifulSoup) -> Dict:
        """Extract social media links"""
        social_links = {}
        social_platforms = {
            'linkedin': ['linkedin.com', 'linkedin'],
            'twitter': ['twitter.com', 'x.com'],
            'facebook': ['facebook.com', 'fb.com'],
            'instagram': ['instagram.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'github': ['github.com'],
            'tiktok': ['tiktok.com']
        }
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href'].lower()
            for platform, domains in social_platforms.items():
                if any(domain in href for domain in domains):
                    social_links[platform] = href
                    break
        
        return social_links
    
    def _detect_technologies(self, soup: BeautifulSoup, response: requests.Response) -> List[str]:
        """Detect technologies used on the website"""
        technologies = []
        
        # Check meta generator
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator and meta_generator.get('content'):
            technologies.append(meta_generator.get('content'))
        
        # Check for common CMS and frameworks
        if 'wp-content' in response.text or 'wordpress' in response.text.lower():
            technologies.append('WordPress')
        
        if 'shopify' in response.text.lower():
            technologies.append('Shopify')
        
        # Check scripts for JS frameworks
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script['src'].lower()
            if 'react' in src:
                technologies.append('React')
            elif 'angular' in src:
                technologies.append('Angular')
            elif 'vue' in src:
                technologies.append('Vue')
            elif 'jquery' in src:
                technologies.append('jQuery')
        
        # Check CSS frameworks
        links = soup.find_all('link', rel='stylesheet')
        for link in links:
            href = link.get('href', '').lower()
            if 'bootstrap' in href:
                technologies.append('Bootstrap')
            elif 'tailwind' in href:
                technologies.append('Tailwind CSS')
            elif 'font-awesome' in href or 'fontawesome' in href:
                technologies.append('Font Awesome')
        
        # Check for analytics
        if 'google-analytics' in response.text or 'gtag' in response.text:
            technologies.append('Google Analytics')
        
        return list(set(technologies))
    
    def _format_as_text(self, company_data: Dict) -> str:
        """Format the scraped data as readable text"""
        text_output = []
        
        # Basic Info
        text_output.append("=" * 60)
        text_output.append("COMPANY BASIC INFORMATION")
        text_output.append("=" * 60)
        basic_info = company_data['basic_info']
        text_output.append(f"Company Name: {basic_info.get('company_name', 'N/A')}")
        text_output.append(f"Website: {basic_info.get('website_url', 'N/A')}")
        text_output.append(f"Title: {basic_info.get('title', 'N/A')}")
        text_output.append(f"Description: {basic_info.get('meta_description', 'N/A')}")
        text_output.append("")
        
        # Contact Info
        text_output.append("=" * 60)
        text_output.append("CONTACT INFORMATION")
        text_output.append("=" * 60)
        contact_info = company_data['contact_info']
        if contact_info.get('contact_page_url'):
            text_output.append(f"Contact Page: {contact_info['contact_page_url']}")
        
        text_output.append("Emails: " + (", ".join(contact_info['emails']) if contact_info['emails'] else "Not found"))
        text_output.append("Phones: " + (", ".join(contact_info['phones']) if contact_info['phones'] else "Not found"))
        text_output.append("")
        
        # Products & Services
        text_output.append("=" * 60)
        text_output.append("PRODUCTS & SERVICES")
        text_output.append("=" * 60)
        products = company_data['products_services']
        if products:
            for i, product in enumerate(products, 1):
                text_output.append(f"{i}. {product}")
        else:
            text_output.append("No products/services found")
        text_output.append("")
        
        # About Section - Show links instead of empty content
        text_output.append("=" * 60)
        text_output.append("ABOUT THE COMPANY")
        text_output.append("=" * 60)
        about_info = company_data['about_section']
        
        # Show about links first
        if about_info.get('about_links'):
            text_output.append("ABOUT PAGES:")
            for link in about_info['about_links']:
                text_output.append(f"- {link['title']}: {link['url']}")
            text_output.append("")
        
        # Then show mission/vision if available
        if about_info.get('mission'):
            text_output.append(f"MISSION: {about_info['mission']}")
            text_output.append("")
        
        if about_info.get('vision'):
            text_output.append(f"VISION: {about_info['vision']}")
            text_output.append("")
        
        # Show about texts if meaningful
        if about_info['about_texts']:
            clean_texts = []
            for text in about_info['about_texts']:
                clean_text = ' '.join(text.strip().split())
                if len(clean_text) > 100:  # Only show meaningful content
                    clean_texts.append(clean_text)
            
            if clean_texts:
                text_output.append("COMPANY DESCRIPTION:")
                for i, text in enumerate(clean_texts[:2], 1):
                    # Show first 300 characters of each meaningful text
                    text_output.append(f"{i}. {text[:300]}...")
                text_output.append("")
        
        # Key Pages
        text_output.append("=" * 60)
        text_output.append("IMPORTANT PAGES")
        text_output.append("=" * 60)
        key_pages = company_data['key_pages']
        if key_pages:
            for page in key_pages[:8]:
                text_output.append(f"- {page['title']}: {page['url']}")
        else:
            text_output.append("No key pages found")
        text_output.append("")
        
        # Social Links
        text_output.append("=" * 60)
        text_output.append("SOCIAL MEDIA LINKS")
        text_output.append("=" * 60)
        social_links = company_data['social_links']
        if social_links:
            for platform, url in social_links.items():
                text_output.append(f"{platform.capitalize()}: {url}")
        else:
            text_output.append("No social media links found")
        text_output.append("")
        
        # Technologies
        text_output.append("=" * 60)
        text_output.append("DETECTED TECHNOLOGIES")
        text_output.append("=" * 60)
        technologies = company_data['technologies']
        if technologies:
            text_output.append(", ".join(technologies))
        else:
            text_output.append("No technologies detected")
        
        return "\n".join(text_output)

# Example usage
if __name__ == "__main__":
    scraper = WebsiteScraper()
    
    # Test with a company website
    test_url = "https://kanini.com/"
    company_data_text = scraper.scrape_company_website(test_url)
    
    print(company_data_text)