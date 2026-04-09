import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List

class SimpleLinkedInScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
    
    def get_company_data(self, linkedin_url: str) -> Dict:
        """Get company data with simple posts extraction"""
        try:
            print(f"Scraping: {linkedin_url}")
            response = self.session.get(linkedin_url, timeout=15)
            
            if response.status_code != 200:
                return {"error": f"Failed to load page: {response.status_code}"}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                "basic_info": self._get_clean_basic_info(soup),
                "overview": self._get_company_overview(soup),
                "about_details": self._get_enhanced_about(soup),
                "posts": self._get_quality_posts(soup),
                "jobs": self._get_real_jobs(soup),
                "people": self._get_people_section(soup),
                "page_links": self._get_dynamic_links(linkedin_url)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_company_slug(self, linkedin_url: str) -> str:
        """Extract company slug from URL"""
        match = re.search(r'company/([^/?]+)', linkedin_url)
        return match.group(1) if match else ""
    
    def _get_clean_basic_info(self, soup: BeautifulSoup) -> Dict:
        """Get clean basic info"""
        info = {}
        
        # Company name
        name_elem = soup.select_one('h1.org-top-card-summary__title, h1.top-card-layout__title')
        if name_elem:
            info['company_name'] = self._clean_text(name_elem.get_text())
        
        # Tagline
        tagline_elem = soup.select_one('.org-top-card-summary__tagline, .top-card-layout__headline')
        if tagline_elem:
            info['tagline'] = self._clean_text(tagline_elem.get_text())
        
        # Followers
        follower_elem = soup.select_one('.org-top-card-summary__follower-count')
        if follower_elem:
            info['followers'] = self._clean_text(follower_elem.get_text())
        
        return info
    
    def _get_company_overview(self, soup: BeautifulSoup) -> Dict:
        """Get company overview section without cutting"""
        overview = {}
        
        # Look for overview sections
        overview_selectors = [
            '.org-about-company-module__company-stats',
            '.org-page-details__card-spacing',
            '.core-section-container',
            '[data-test-id="about-us"]',
            '.org-about-us-organization-description__text'
        ]
        
        for selector in overview_selectors:
            overview_elem = soup.select_one(selector)
            if overview_elem:
                text_content = self._clean_text(overview_elem.get_text())
                if len(text_content) > 50:
                    overview['summary'] = text_content
                    break
        
        return overview
    
    def _get_enhanced_about(self, soup: BeautifulSoup) -> Dict:
        """Get enhanced about information with more content"""
        about = {}
        
        # Extract all text and parse manually
        full_text = soup.get_text()
        
        # Website
        website_match = re.search(r'https?://[^\s"\']+', full_text)
        if website_match:
            about['website'] = website_match.group(0)
        
        # Industry
        industry_match = re.search(r'Industry\s*([^\n]+)', full_text)
        if industry_match:
            about['industry'] = self._clean_text(industry_match.group(1))
        
        # Company size
        size_match = re.search(r'Company size\s*([^\n]+)', full_text)
        if not size_match:
            size_match = re.search(r'(\d+(?:,\d+)*\s*-\s*\d+(?:,\d+)*|\d+(?:,\d+)*\+?)\s*employees', full_text, re.IGNORECASE)
        if size_match:
            about['company_size'] = self._clean_text(size_match.group(1))
        
        # Headquarters
        hq_match = re.search(r'Headquarters\s*([^\n]+)', full_text)
        if hq_match:
            about['headquarters'] = self._clean_text(hq_match.group(1))
        
        # Founded
        founded_match = re.search(r'Founded\s*(\d{4})', full_text)
        if founded_match:
            about['founded'] = founded_match.group(1)
        
        # Specialties
        specialties_match = re.search(r'Specialties\s*([^\n]+(?:\n[^\n]+)*)', full_text)
        if specialties_match:
            about['specialties'] = self._clean_text(specialties_match.group(1))
        
        # Associated members
        members_match = re.search(r'(\d+(?:,\d+)*)\s+associated members', full_text)
        if members_match:
            about['associated_members'] = members_match.group(1)
        
        return about
    
    def _get_quality_posts(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract only quality posts that are actual company updates"""
        posts = []
        
        print("Extracting quality posts...")
        
        # Method 1: Look for structured post containers with engagement
        post_containers = soup.select('[data-urn*="activity"], .feed-shared-update-v2, .occludable-update')
        
        for container in post_containers:
            post_data = self._extract_quality_post(container)
            if post_data and post_data.get('content'):
                posts.append(post_data)
                if len(posts) >= 5:
                    break
        
        # Method 2: Look for posts with engagement metrics
        if len(posts) < 3:
            engagement_containers = soup.select('.social-details-social-counts, [class*="reaction"], [class*="comment"]')
            for container in engagement_containers:
                post_data = self._extract_post_from_engagement(container)
                if post_data and post_data.get('content') and not any(p['content'][:50] == post_data['content'][:50] for p in posts):
                    posts.append(post_data)
                    if len(posts) >= 5:
                        break
        
        # Method 3: Only include posts that have actual content and look like real updates
        if len(posts) < 3:
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = self._clean_text(div.get_text())
                if self._is_high_quality_post(text):
                    post_data = self._create_quality_post(div, text)
                    if post_data and not any(p.get('content', '')[:50] == post_data['content'][:50] for p in posts):
                        posts.append(post_data)
                        if len(posts) >= 5:
                            break
        
        print(f"Total quality posts extracted: {len(posts)}")
        return posts[:5]  # Return up to 5 quality posts
    
    def _extract_quality_post(self, container) -> Dict:
        """Extract quality post from structured container"""
        post_data = {}
        
        # Get content from post-specific selectors
        content_selectors = [
            '.feed-shared-text',
            '.update-components-text',
            '.feed-shared-inline-show-more-text',
            '.attributed-text-segment-list__content'
        ]
        
        content_parts = []
        for selector in content_selectors:
            elements = container.select(selector)
            for elem in elements:
                text = self._clean_text(elem.get_text())
                if text and len(text) > 30 and self._is_post_content(text):
                    content_parts.append(text)
        
        if content_parts:
            full_content = ' '.join(content_parts)
            cleaned_content = self._clean_post_content(full_content)
            if len(cleaned_content) > 50:
                post_data['content'] = cleaned_content[:400] + "..." if len(cleaned_content) > 400 else cleaned_content
        
        # Get timestamp
        time_elem = container.select_one('.feed-shared-actor__sub-description, .update-components-actor__sub-description')
        if time_elem:
            time_text = self._clean_text(time_elem.get_text())
            timestamp = self._extract_timestamp_from_text(time_text)
            if timestamp:
                post_data['timestamp'] = timestamp
        
        # Get engagement
        engagement = {}
        reactions_elem = container.select_one('.social-details-social-counts__reactions')
        if reactions_elem:
            engagement['reactions'] = self._clean_text(reactions_elem.get_text())
        
        comments_elem = container.select_one('.social-details-social-counts__comments')
        if comments_elem:
            engagement['comments'] = self._clean_text(comments_elem.get_text())
        
        if engagement:
            post_data['engagement'] = engagement
        
        # Get post URL
        link = container.find('a', href=re.compile(r'(feed/update|activity|posts)'))
        if link and link.get('href'):
            href = link['href']
            post_data['post_url'] = f"https://www.linkedin.com{href}" if href.startswith('/') else href
        
        return post_data if post_data.get('content') else {}
    
    def _extract_post_from_engagement(self, container) -> Dict:
        """Extract post from engagement container"""
        # Look for nearby content that could be a post
        parent = container.parent
        for _ in range(3):
            if parent:
                # Look for post content in siblings or parent
                content_elements = parent.select('.feed-shared-text, .update-components-text')
                for elem in content_elements:
                    text = self._clean_text(elem.get_text())
                    if text and len(text) > 50 and self._is_post_content(text):
                        return {
                            'content': text[:400] + "..." if len(text) > 400 else text,
                            'timestamp': 'Recent'
                        }
                parent = parent.parent
        return {}
    
    def _create_quality_post(self, element, text: str) -> Dict:
        """Create quality post only if it meets criteria"""
        # Clean and validate the text
        cleaned = self._clean_post_content(text)
        if not self._is_high_quality_post(cleaned):
            return {}
        
        post_data = {
            'content': cleaned[:400] + "..." if len(cleaned) > 400 else cleaned,
            'timestamp': 'Recent'
        }
        
        # Try to find post URL
        link = element.find('a', href=re.compile(r'(feed/update|activity|posts)'))
        if link and link.get('href'):
            href = link['href']
            post_data['post_url'] = f"https://www.linkedin.com{href}" if href.startswith('/') else href
        
        return post_data
    
    def _is_high_quality_post(self, text: str) -> bool:
        """Check if text is a high quality post"""
        if len(text) < 80 or len(text) > 1500:
            return False
        
        # Must contain post-like content
        post_indicators = [
            'announcing', 'proud', 'excited', 'happy', 'delighted',
            'milestone', 'innovation', 'collaboration', 'hosted', 'launched',
            'released', 'partnership', 'achievement', 'success', 'growth',
            'team', 'customer', 'client', 'project', 'solution',
            'congratulations', 'celebrating', 'honored', 'thrilled',
            'welcome', 'introducing', 'joined', 'event', 'meetup',
            'webinar', 'workshop', 'conference'
        ]
        
        # Must NOT contain non-post content
        non_post_indicators = [
            'location', 'address', 'get directions', 'employees at',
            'copyright', 'privacy', 'terms', 'cookie', 'policy',
            'navigation', 'menu', 'sign in', 'follow', 'linkedin',
            'primary', 'rattha', 'century', 'blvd', 'nashville',
            'chennai', 'tamil nadu', 'zip', 'postal'
        ]
        
        text_lower = text.lower()
        
        # Must have at least 2 post indicators
        post_count = sum(1 for indicator in post_indicators if indicator in text_lower)
        if post_count < 2:
            return False
        
        # Must not have any non-post indicators
        if any(indicator in text_lower for indicator in non_post_indicators):
            return False
        
        return True
    
    def _is_post_content(self, text: str) -> bool:
        """Check if text looks like post content"""
        text_lower = text.lower()
        
        # Exclude location, employee lists, etc.
        if any(phrase in text_lower for phrase in [
            'get directions', 'employees at', 'primary location',
            'nashville, tennessee', 'chennai, tamil nadu'
        ]):
            return False
        
        return len(text) > 50 and len(text) < 1000
    
    def _clean_post_content(self, text: str) -> str:
        """Clean post content"""
        cleaned = re.sub(r'\s+', ' ', text)
        cleaned = re.sub(r'\.{3,}', '...', cleaned)
        return self._clean_text(cleaned)
    
    def _extract_timestamp_from_text(self, text: str) -> str:
        """Extract timestamp from text"""
        patterns = [
            r'(\d+\s*(?:min|mins|minute|minutes)\s*ago)',
            r'(\d+\s*(?:hour|hours)\s*ago)',
            r'(\d+\s*(?:day|days)\s*ago)',
            r'(\d+\s*(?:week|weeks)\s*ago)',
            r'(\d+\s*(?:month|months)\s*ago)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        
        return ""
    
    def _get_real_jobs(self, soup: BeautifulSoup) -> List[Dict]:
        """Get real job listings from the company page"""
        jobs = []
        
        print("Extracting real jobs...")
        
        # Multiple selectors for jobs
        job_selectors = [
            '.org-jobs-card__job-title',
            '.job-card-list__title',
            '[class*="job-title"]',
            '[data-control-name*="job"]',
            '.artdeco-entity-lockup__title',
            '.job-card-container__link'
        ]
        
        for selector in job_selectors:
            job_elements = soup.select(selector)
            for job_elem in job_elements:
                job_text = self._clean_text(job_elem.get_text())
                
                if (job_text and 
                    len(job_text) > 3 and 
                    len(job_text) < 100 and
                    not any(word in job_text.lower() for word in ['see', 'view', 'all', 'jobs']) and
                    not job_text.isdigit()):
                    
                    # Find job URL
                    job_link = job_elem.find_parent('a', href=True)
                    if job_link:
                        href = job_link['href']
                        job_url = f"https://www.linkedin.com{href}" if href.startswith('/') else href
                        
                        # Find location
                        location = "Multiple Locations"
                        location_elem = job_elem.find_next(string=re.compile(r'[A-Za-z]+(?:,\s*[A-Za-z]+)*'))
                        if location_elem:
                            location_text = self._clean_text(location_elem)
                            if len(location_text) > 2 and len(location_text) < 50:
                                location = location_text
                        
                        jobs.append({
                            'title': job_text,
                            'location': location,
                            'url': job_url
                        })
                        
                        if len(jobs) >= 6:
                            return jobs
        
        # If no specific jobs found, look for jobs page link
        if not jobs:
            jobs_link = soup.find('a', href=re.compile(r'jobs'), string=re.compile(r'jobs', re.IGNORECASE))
            if jobs_link:
                href = jobs_link['href']
                jobs.append({
                    'title': 'View all company jobs',
                    'location': 'Multiple locations',
                    'url': f"https://www.linkedin.com{href}" if href.startswith('/') else href
                })
        
        return jobs[:6]
    
    def _get_people_section(self, soup: BeautifulSoup) -> Dict:
        """Get people/employees section data"""
        people_data = {}
        
        # Employee count
        full_text = soup.get_text()
        employees_match = re.search(r'(\d+(?:,\d+)*)\s*employees? on LinkedIn', full_text)
        if employees_match:
            people_data['linkedin_employees'] = employees_match.group(1)
        
        return people_data
    
    def _get_dynamic_links(self, linkedin_url: str) -> Dict:
        """Get dynamic links based on the company URL"""
        # Extract company slug from URL
        match = re.search(r'company/([^/?]+)', linkedin_url)
        if match:
            company_slug = match.group(1)
        else:
            return {}
        
        links = {
            'posts_page': f'https://www.linkedin.com/company/{company_slug}/posts/',
            'people_page': f'https://www.linkedin.com/company/{company_slug}/people/',
            'jobs_page': f'https://www.linkedin.com/company/{company_slug}/jobs/',
            'about_page': f'https://www.linkedin.com/company/{company_slug}/about/'
        }
        
        return links
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        cleaned = ' '.join(text.split())
        return cleaned.strip()
    
    def format_output(self, data: Dict) -> str:
        """Enhanced output format"""
        if "error" in data:
            return f"Error: {data['error']}"
        
        output = []
        output.append("=" * 70)
        output.append("ENHANCED LINKEDIN COMPANY PROFILE")
        output.append("=" * 70)
        output.append("")
        
        # Basic Info
        basic = data.get('basic_info', {})
        output.append("🏢 COMPANY INFORMATION")
        output.append("-" * 30)
        if basic.get('company_name'):
            output.append(f"Name: {basic['company_name']}")
        if basic.get('tagline'):
            output.append(f"Industry: {basic['tagline']}")
        if basic.get('followers'):
            output.append(f"Followers: {basic['followers']}")
        output.append("")
        
        # Overview Section
        overview = data.get('overview', {})
        if overview:
            output.append("📊 COMPANY OVERVIEW")
            output.append("-" * 30)
            if overview.get('summary'):
                output.append(overview['summary'])
                output.append("")
        
        # About Details
        about = data.get('about_details', {})
        output.append("ℹ️ COMPANY DETAILS")
        output.append("-" * 30)
        if about.get('website'):
            output.append(f"Website: {about['website']}")
        if about.get('industry'):
            output.append(f"Industry: {about['industry']}")
        if about.get('company_size'):
            output.append(f"Company Size: {about['company_size']}")
        if about.get('headquarters'):
            output.append(f"Headquarters: {about['headquarters']}")
        if about.get('founded'):
            output.append(f"Founded: {about['founded']}")
        if about.get('associated_members'):
            output.append(f"LinkedIn Members: {about['associated_members']}")
        if about.get('specialties'):
            output.append(f"Specialties: {about['specialties']}")
        output.append("")
        
        # People Section
        people = data.get('people', {})
        if people:
            output.append("👥 PEOPLE & EMPLOYEES")
            output.append("-" * 30)
            if people.get('linkedin_employees'):
                output.append(f"Employees on LinkedIn: {people['linkedin_employees']}")
            output.append("")
        
        # Posts Section
        posts = data.get('posts', [])
        page_links = data.get('page_links', {})
        output.append("📝 RECENT POSTS & ACTIVITY")
        output.append("-" * 30)
        
        if page_links.get('posts_page'):
            output.append(f"🔗 View All Posts: {page_links['posts_page']}")
            output.append("")
        
        if posts:
            for i, post in enumerate(posts, 1):
                output.append(f"📝 Post {i}:")
                output.append(f"   {post['content']}")
                
                if post.get('engagement'):
                    engagement = post['engagement']
                    if engagement.get('reactions'):
                        output.append(f"   👍 {engagement['reactions']} reactions")
                    if engagement.get('comments'):
                        output.append(f"   💬 {engagement['comments']} comments")
                
                if post.get('post_url'):
                    output.append(f"   🔗 {post['post_url']}")
                
                output.append("")
        else:
            output.append("No recent posts available")
            output.append("")
        
        # Jobs Section
        jobs = data.get('jobs', [])
        output.append("💼 CAREER OPPORTUNITIES")
        output.append("-" * 30)
        
        if page_links.get('jobs_page'):
            output.append(f"🔗 View All Jobs: {page_links['jobs_page']}")
            output.append("")
        
        if jobs:
            output.append("Current Openings:")
            output.append("")
            for job in jobs:
                output.append(f"💼 {job['title']}")
                output.append(f"   📍 {job.get('location', 'Location not specified')}")
                output.append(f"   🔗 {job['url']}")
                output.append("")
        else:
            output.append("No specific job listings found")
            output.append("")
        
        # Quick Links
        if page_links:
            output.append("🔗 QUICK LINKS")
            output.append("-" * 30)
            for link_type, url in page_links.items():
                if link_type == 'people_page':
                    output.append(f"👥 People Page: {url}")
                elif link_type == 'about_page':
                    output.append(f"ℹ️ About Page: {url}")
                elif link_type == 'jobs_page':
                    output.append(f"💼 Jobs Page: {url}")
                elif link_type == 'posts_page':
                    output.append(f"📝 Posts Page: {url}")
            output.append("")
        
        output.append("=" * 70)
        return "\n".join(output)

# Test the scraper
if __name__ == "__main__":
    scraper = SimpleLinkedInScraper()
    
    print("SCRAPING LINKEDIN PROFILE...")
    data = scraper.get_company_data("https://www.linkedin.com/company/tata-consultancy-services/")
    print(scraper.format_output(data))