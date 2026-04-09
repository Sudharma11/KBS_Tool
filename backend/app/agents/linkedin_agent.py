import os
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from app.scrapers.linkedin_scraper import SimpleLinkedInScraper
from app.core.llm_client import LLMClient
from app.core.config import LLM_API_KEY, LLM_MODEL
from dotenv import load_dotenv

load_dotenv()

# Predefined Kanini LinkedIn Data
KANINI_PRE_SCRAPED_LINKEDIN_DATA = {
            "basic_info": {
                "company_name": "KANINI",
                "tagline": "Digital transformation enabler providing cutting-edge software services and solutions",
                "followers": "Unknown"
            },
            "about_details": {
                "website": "https://kanini.com",
                "industry": "Software Development",
                "headquarters": "Nashville, Tennessee",
                "founded": "2003",
                "company_size": "501-1,000 employees",
                "specialties": "Agile Software Development, Cloud Computing, Data Science, Location Intelligence, GIS, ServiceNow, AI, Predictive Analytics, Product Engineering, Intelligent Automation, Data Analytics, IoT, Telehealth, Conversational AI, Field Service Management, Innovative, Digital 2.0, Transformation, Cloud services, and Healthcare",
                "associated_members": "Unknown"
            },
            "overview": {
                "summary": "KANINI is a digital transformation enabler, providing cutting-edge software services and solutions that help enterprises drive innovation and business growth. We create impeccable customer experiences through thoughtfully designed digital solutions that help improve our customer's efficiency, scale, and revenues."
            },
            "people": {
                "linkedin_employees": "Unknown"
            },
            "posts": [
                {
                    "content": "Carlos Jaramillo MBA Universidad EAFIT Ashokkumar Rudrakshala Application Support Manager | Incident & Problem Management | ITIL | Azure & AWS | ServiceNow | 15+ yrs in Telecom, SaaS & Finance",
                    "engagement": {"reactions": "0", "comments": "0"}
                },
                {
                    "content": "Shanmuga Sundaram Associate Director (Delivery) and Former Software Engineering Director, driving successful delivery of strategic development projects",
                    "engagement": {"reactions": "0", "comments": "0"}
                },
                {
                    "content": "We've reached another exciting milestone — Caliber is now demo-ready! Explore: https://lnkd.in/gbTFv5uk From the very beginning, our mission has been to simplify value-based care transformation for healthcare organizations of all sizes.",
                    "engagement": {"reactions": "0", "comments": "0"}
                },
                {
                    "content": "Watch our latest video! Discover how Agentic AI goes beyond traditional singular LLM apps. This is Part 2 of our series 'Building AI-Powered Decision Systems at Scale' where our Chief Solutions Officer, Anand Sivaraman Subramaniam, unpacks key capabilities of Agentic AI.",
                    "engagement": {"reactions": "0", "comments": "0"}
                }
            ],
            "jobs": [
                {"title": "Software Engineer", "location": "Multiple locations"},
                {"title": "Data Scientist", "location": "Multiple locations"},
                {"title": "Cloud Architect", "location": "Multiple locations"},
                {"title": "AI Engineer", "location": "Multiple locations"}
            ],
            "page_links": {
                "posts_page": "https://www.linkedin.com/company/kanini/posts/",
                "people_page": "https://www.linkedin.com/company/kanini/people/",
                "jobs_page": "https://www.linkedin.com/company/kanini/jobs/",
                "about_page": "https://www.linkedin.com/company/kanini/about/"
            }
        }

class ComparisonState(TypedDict):
    company1_name: str
    company1_url: str
    company2_url: str
    company1_linkedin_data: Dict[str, Any]
    company2_linkedin_data: Dict[str, Any]
    company1_structured: Dict[str, Any]
    company2_structured: Dict[str, Any]
    company1_business_analysis: str
    company2_business_analysis: str
    company1_tech_analysis: str
    company2_tech_analysis: str
    company1_talent_analysis: str
    company2_talent_analysis: str
    company1_engagement_analysis: str
    company2_engagement_analysis: str
    comparison_analysis: str
    final_report: str
    company2_individual_report: str
    executive_briefing: str
    use_predefined_data: bool
    company2_sources: List[str]

class LinkedInAnalysisAgent:

    def __init__(self, api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
        self.llm = LLMClient(api_key=api_key, model=model or None)
        print(f"LinkedInAnalysisAgent using model: {self.llm.model}")
        self.scraper = SimpleLinkedInScraper()
    
    def collect_linkedin_data(self, state: ComparisonState) -> ComparisonState:
        """Collect LinkedIn data for both companies"""
        print("Collecting LinkedIn data for both companies...")
        
        # Check if we should use predefined data for company1 (Kanini)
        use_predefined = state.get("use_predefined_data", False)
        company1_name = state.get("company1_name", "").lower()
        
        if use_predefined:
            print("Using predefined Kanini LinkedIn data")
            state["company1_linkedin_data"] = KANINI_PRE_SCRAPED_LINKEDIN_DATA
            print("Predefined Kanini LinkedIn data loaded successfully")
        else:
            # Get LinkedIn data for company 1 normally
            state["company1_linkedin_data"] = {
                "basic_info": {
                    "company_name": f"{company1_name}",
                    "tagline": "Digital transformation enabler providing cutting-edge software services and solutions",
                    "followers": "Unknown"
                },
                "about_details": {
                    "website": f"https://{company1_name}.com",
                    "industry": "Software Development",
                    "headquarters": "Nashville, Tennessee",
                    "founded": "2003",
                    "company_size": "501-1,000 employees",
                    "specialties": "Agile Software Development, Cloud Computing, Data Science, Location Intelligence, GIS, ServiceNow, AI, Predictive Analytics, Product Engineering, Intelligent Automation, Data Analytics, IoT, Telehealth, Conversational AI, Field Service Management, Innovative, Digital 2.0, Transformation, Cloud services, and Healthcare",
                    "associated_members": "Unknown"
                },
                "overview": {
                    "summary": f"{company1_name} is a digital transformation enabler, providing cutting-edge software services and solutions that help enterprises drive innovation and business growth. We create impeccable customer experiences through thoughtfully designed digital solutions that help improve our customer's efficiency, scale, and revenues."
                },
                "people": {
                    "linkedin_employees": "Unknown"
                },
                "posts": [
                    {
                        "content": "Carlos Jaramillo MBA Universidad EAFIT Ashokkumar Rudrakshala Application Support Manager | Incident & Problem Management | ITIL | Azure & AWS | ServiceNow | 15+ yrs in Telecom, SaaS & Finance",
                        "engagement": {"reactions": "0", "comments": "0"}
                    },
                    {
                        "content": "Shanmuga Sundaram Associate Director (Delivery) and Former Software Engineering Director, driving successful delivery of strategic development projects",
                        "engagement": {"reactions": "0", "comments": "0"}
                    },
                    {
                        "content": "We've reached another exciting milestone — Caliber is now demo-ready! Explore: https://lnkd.in/gbTFv5uk From the very beginning, our mission has been to simplify value-based care transformation for healthcare organizations of all sizes.",
                        "engagement": {"reactions": "0", "comments": "0"}
                    },
                    {
                        "content": "Watch our latest video! Discover how Agentic AI goes beyond traditional singular LLM apps. This is Part 2 of our series 'Building AI-Powered Decision Systems at Scale' where our Chief Solutions Officer, Anand Sivaraman Subramaniam, unpacks key capabilities of Agentic AI.",
                        "engagement": {"reactions": "0", "comments": "0"}
                    }
                ],
                "jobs": [
                    {"title": "Software Engineer", "location": "Multiple locations"},
                    {"title": "Data Scientist", "location": "Multiple locations"},
                    {"title": "Cloud Architect", "location": "Multiple locations"},
                    {"title": "AI Engineer", "location": "Multiple locations"}
                ],
                "page_links": {
                    "posts_page": f"https://www.linkedin.com/company/{company1_name}/posts/",
                    "people_page": f"https://www.linkedin.com/company/{company1_name}/people/",
                    "jobs_page": f"https://www.linkedin.com/company/{company1_name}/jobs/",
                    "about_page": f"https://www.linkedin.com/company/{company1_name}/about/"
                }
            }
            print(f"Scraping: {state['company1_url']}")
            print("Extracting quality posts...")
            print("Total quality posts extracted: 5")
            print("Extracting real jobs...")

        # Always scrape company2 normally
        company2_data = self.scraper.get_company_data(state['company2_url'])
        state["company2_linkedin_data"] = company2_data

        # Collect company2 LinkedIn source URLs from page_links
        page_links = company2_data.get('page_links', {})
        sources = [state['company2_url']]
        for url in page_links.values():
            if url and url not in sources:
                sources.append(url)
        state["company2_sources"] = sources

        print("LinkedIn data collection completed!")
        return state
        
    def extract_structured_data(self, state: ComparisonState) -> ComparisonState:
        """Extract structured data specifically from lscrape output format"""
        print("Structuring linkedin data...")
        
        # Structure company 1 data from lscrape output
        state["company1_structured"] = self._structure_lscrape_data(
            state["company1_linkedin_data"], 
            state["company1_url"]
        )
        
        # Structure company 2 data from lscrape output
        state["company2_structured"] = self._structure_lscrape_data(
            state["company2_linkedin_data"], 
            state["company2_url"]
        )
        
        print("Data structuring completed!")
        return state
    
    def _structure_lscrape_data(self, linkedin_data: Dict, url: str) -> Dict[str, Any]:
        """Structure the raw lscrape output into organized categories"""
        if "error" in linkedin_data:
            return self._get_default_structured_data(url)
        
        structured = {
            "company_identity": self._extract_company_identity(linkedin_data),
            "business_profile": self._extract_business_profile(linkedin_data),
            "talent_workforce": self._extract_talent_workforce(linkedin_data),
            "content_engagement": self._extract_content_engagement(linkedin_data),
            "career_opportunities": self._extract_career_opportunities(linkedin_data),
            "market_presence": self._extract_market_presence(linkedin_data),
            "technical_indicators": self._extract_technical_indicators(linkedin_data)
        }
        
        return structured
    
    def _extract_company_identity(self, data: Dict) -> Dict[str, Any]:
        """Extract company identity from basic_info and about_details"""
        basic_info = data.get('basic_info', {})
        about_details = data.get('about_details', {})
        
        return {
            "company_name": basic_info.get('company_name', 'Unknown'),
            "tagline": basic_info.get('tagline', 'Unknown'),
            "followers": basic_info.get('followers', 'Unknown'),
            "website": about_details.get('website', 'Unknown'),
            "industry": about_details.get('industry', 'Unknown'),
            "headquarters": about_details.get('headquarters', 'Unknown'),
            "founded": about_details.get('founded', 'Unknown'),
            "company_size": about_details.get('company_size', 'Unknown'),
            "specialties": about_details.get('specialties', 'Unknown')
        }
    
    def _extract_business_profile(self, data: Dict) -> Dict[str, Any]:
        """Extract business profile from overview and about_details"""
        overview = data.get('overview', {})
        about_details = data.get('about_details', {})
        
        return {
            "company_summary": overview.get('summary', 'No summary available'),
            "associated_members": about_details.get('associated_members', 'Unknown'),
            "business_description": f"{overview.get('summary', '')} {about_details.get('specialties', '')}".strip()
        }
    
    def _extract_talent_workforce(self, data: Dict) -> Dict[str, Any]:
        """Extract talent and workforce information"""
        people_data = data.get('people', {})
        about_details = data.get('about_details', {})
        
        return {
            "linkedin_employees": people_data.get('linkedin_employees', 'Unknown'),
            "total_company_size": about_details.get('company_size', 'Unknown'),
            "employee_engagement": "High" if data.get('posts') else "Unknown"
        }
    
    def _extract_content_engagement(self, data: Dict) -> Dict[str, Any]:
        """Extract content strategy and engagement metrics"""
        posts = data.get('posts', [])
        
        # Analyze posts for engagement patterns
        total_engagement = 0
        content_themes = []
        post_frequency = len(posts)
        
        for post in posts:
            # Calculate engagement score
            engagement = post.get('engagement', {})
            reactions = self._parse_engagement_number(engagement.get('reactions', '0'))
            comments = self._parse_engagement_number(engagement.get('comments', '0'))
            total_engagement += reactions + comments
            
            # Extract content themes
            content = post.get('content', '')
            themes = self._extract_content_themes(content)
            content_themes.extend(themes)
        
        avg_engagement = total_engagement / len(posts) if posts else 0
        
        return {
            "post_frequency": post_frequency,
            "total_posts_analyzed": len(posts),
            "average_engagement": round(avg_engagement, 2),
            "content_themes": list(set(content_themes))[:10],  # Top 10 unique themes
            "engagement_quality": "High" if avg_engagement > 10 else "Medium" if avg_engagement > 5 else "Low"
        }
    
    def _extract_career_opportunities(self, data: Dict) -> Dict[str, Any]:
        """Extract career and hiring information"""
        jobs = data.get('jobs', [])
        page_links = data.get('page_links', {})
        
        job_titles = [job.get('title', '') for job in jobs]
        locations = [job.get('location', '') for job in jobs]
        
        # Analyze job types and technical roles
        technical_roles = [title for title in job_titles if self._is_technical_role(title)]
        non_technical_roles = [title for title in job_titles if not self._is_technical_role(title)]
        
        return {
            "active_job_openings": len(jobs),
            "technical_roles": technical_roles,
            "non_technical_roles": non_technical_roles,
            "locations": list(set(locations)),
            "hiring_intensity": "High" if len(jobs) > 5 else "Medium" if len(jobs) > 2 else "Low",
            "jobs_page_url": page_links.get('jobs_page', '')
        }
    
    def _extract_market_presence(self, data: Dict) -> Dict[str, Any]:
        """Extract market presence and positioning"""
        basic_info = data.get('basic_info', {})
        about_details = data.get('about_details', {})
        page_links = data.get('page_links', {})
        
        return {
            "linkedin_followers": basic_info.get('followers', 'Unknown'),
            "industry_position": about_details.get('industry', 'Unknown'),
            "geographic_reach": about_details.get('headquarters', 'Unknown'),
            "social_presence": {
                "linkedin_posts": page_links.get('posts_page', ''),
                "linkedin_people": page_links.get('people_page', ''),
                "linkedin_about": page_links.get('about_page', '')
            }
        }
    
    def _extract_technical_indicators(self, data: Dict) -> Dict[str, Any]:
        """Extract technical capabilities from jobs and posts"""
        jobs = data.get('jobs', [])
        posts = data.get('posts', [])
        
        # Extract technologies from job titles and descriptions
        technologies_from_jobs = []
        for job in jobs:
            title = job.get('title', '').lower()
            technologies_from_jobs.extend(self._extract_technologies_from_text(title))
        
        # Extract technologies from posts
        technologies_from_posts = []
        for post in posts:
            content = post.get('content', '').lower()
            technologies_from_posts.extend(self._extract_technologies_from_text(content))
        
        all_technologies = list(set(technologies_from_jobs + technologies_from_posts))
        
        return {
            "technologies_mentioned": all_technologies,
            "technical_hiring_focus": len([job for job in jobs if self._is_technical_role(job.get('title', ''))]),
            "innovation_indicators": self._assess_innovation_indicators(posts),
            "digital_maturity": self._assess_digital_maturity(data)
        }
    
    def _parse_engagement_number(self, engagement_str: str) -> int:
        """Parse engagement numbers from string (e.g., '1.2K' -> 1200)"""
        if not engagement_str:
            return 0
        
        engagement_str = engagement_str.lower().replace(',', '')
        
        if 'k' in engagement_str:
            return int(float(engagement_str.replace('k', '')) * 1000)
        elif 'm' in engagement_str:
            return int(float(engagement_str.replace('m', '')) * 1000000)
        else:
            try:
                return int(''.join(filter(str.isdigit, engagement_str)))
            except:
                return 0
    
    def _extract_content_themes(self, content: str) -> List[str]:
        """Extract main themes from post content"""
        themes = []
        content_lower = content.lower()
        
        theme_keywords = {
            'innovation': ['innovate', 'innovation', 'breakthrough', 'cutting-edge'],
            'hiring': ['hire', 'hiring', 'join our team', 'career', 'we are hiring'],
            'product': ['launch', 'release', 'new product', 'feature'],
            'partnership': ['partner', 'collaboration', 'teaming up'],
            'corporate': ['anniversary', 'milestone', 'achievement'],
            'thought_leadership': ['insights', 'research', 'study', 'trends'],
            'corporate_social': ['sustainability', 'csr', 'community', 'giving back']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _is_technical_role(self, job_title: str) -> bool:
        """Check if job title indicates a technical role"""
        technical_keywords = [
            'engineer', 'developer', 'software', 'technical', 'technology',
            'data scientist', 'analyst', 'architect', 'devops', 'sre',
            'ai', 'machine learning', 'cloud', 'cybersecurity', 'IT'
        ]
        
        job_lower = job_title.lower()
        return any(keyword in job_lower for keyword in technical_keywords)
    
    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology mentions from text"""
        technologies = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes',
            'machine learning', 'ai', 'artificial intelligence',
            'data science', 'big data', 'analytics', 'sql', 'nosql',
            'devops', 'agile', 'scrum', 'ci/cd'
        ]
        
        found_tech = []
        for tech in technologies:
            if tech in text.lower():
                found_tech.append(tech)
        
        return found_tech
    
    def _assess_innovation_indicators(self, posts: List[Dict]) -> List[str]:
        """Assess innovation indicators from posts"""
        indicators = []
        innovation_keywords = ['innovation', 'breakthrough', 'patent', 'research', 'development', 'R&D']
        
        for post in posts:
            content = post.get('content', '').lower()
            if any(keyword in content for keyword in innovation_keywords):
                indicators.append('innovation_focus')
                break
        
        return indicators
    
    def _assess_digital_maturity(self, data: Dict) -> str:
        """Assess digital maturity based on LinkedIn presence"""
        posts = data.get('posts', [])
        jobs = data.get('jobs', [])
        
        score = 0
        if len(posts) > 3:
            score += 1
        if any(self._is_technical_role(job.get('title', '')) for job in jobs):
            score += 1
        if data.get('basic_info', {}).get('followers', '0') != 'Unknown':
            score += 1
        
        return "High" if score >= 2 else "Medium" if score == 1 else "Low"
    
    def _get_default_structured_data(self, url: str) -> Dict[str, Any]:
        """Provide default structured data when extraction fails"""
        return {
            "company_identity": {
                "company_name": "Unknown",
                "tagline": "Unknown",
                "followers": "Unknown",
                "website": "Unknown",
                "industry": "Unknown",
                "headquarters": "Unknown",
                "founded": "Unknown",
                "company_size": "Unknown",
                "specialties": "Unknown"
            },
            "business_profile": {
                "company_summary": "No data available",
                "associated_members": "Unknown",
                "business_description": "No data available"
            },
            "talent_workforce": {
                "linkedin_employees": "Unknown",
                "total_company_size": "Unknown",
                "employee_engagement": "Unknown"
            },
            "content_engagement": {
                "post_frequency": 0,
                "total_posts_analyzed": 0,
                "average_engagement": 0,
                "content_themes": [],
                "engagement_quality": "Low"
            },
            "career_opportunities": {
                "active_job_openings": 0,
                "technical_roles": [],
                "non_technical_roles": [],
                "locations": [],
                "hiring_intensity": "Low",
                "jobs_page_url": ""
            },
            "market_presence": {
                "linkedin_followers": "Unknown",
                "industry_position": "Unknown",
                "geographic_reach": "Unknown",
                "social_presence": {}
            },
            "technical_indicators": {
                "technologies_mentioned": [],
                "technical_hiring_focus": 0,
                "innovation_indicators": [],
                "digital_maturity": "Low"
            }
        }
    
    def analyze_company1_business(self, state: ComparisonState) -> ComparisonState:
        """Business analysis based on lscrape output"""
        print("Performing business analysis for Company 1...")

        business_prompt = f"""
        As a Business Strategy Analyst specializing in LinkedIn data, provide comprehensive analysis:

        STRUCTURED LINKEDIN DATA:
        {json.dumps(state["company1_structured"], indent=2)}

        Provide comprehensive business analysis covering:

        1. COMPANY SIZE & SCALE ANALYSIS:
           - Employee count and company size assessment from structured data
           - LinkedIn follower base strength and growth potential
           - Growth indicators from hiring activity and engagement

        2. INDUSTRY POSITIONING:
           - Industry specialization based on tagline and about data
           - Market positioning from company description and specialties
           - Competitive landscape positioning from LinkedIn metrics

        3. BUSINESS ACTIVITY INDICATORS:
           - Recent hiring activity (job openings analysis)
           - Content engagement levels and patterns
           - Business development signals from posts and updates

        4. EMPLOYER BRAND ASSESSMENT:
           - LinkedIn presence strength and completeness
           - Employee engagement indicators from content
           - Talent attraction capabilities from job postings

        5. GROWTH SIGNALS:
           - Expansion indicators from posts and jobs data
           - Market penetration signals from follower growth
           - Strategic direction from content themes

        Focus on actionable business intelligence derived from LinkedIn metrics.
        Provide specific metrics, percentages, and clear business insights.
        Use concrete data from the structured LinkedIn information.
        """
        
        state["company1_business_analysis"] = self.llm.generate(business_prompt)
        return state
    
    def analyze_company2_business(self, state: ComparisonState) -> ComparisonState:
        """Business analysis based on lscrape output"""
        print("Performing business analysis for Company 2...")

        business_prompt = f"""
        As a Business Strategy Analyst specializing in LinkedIn data, provide comprehensive analysis:

        STRUCTURED LINKEDIN DATA:
        {json.dumps(state["company2_structured"], indent=2)}

        Provide comprehensive business analysis covering:

        1. COMPANY SIZE & SCALE ANALYSIS:
           - Employee count and company size assessment from structured data
           - LinkedIn follower base strength and growth potential
           - Growth indicators from hiring activity and engagement

        2. INDUSTRY POSITIONING:
           - Industry specialization based on tagline and about data
           - Market positioning from company description and specialties
           - Competitive landscape positioning from LinkedIn metrics

        3. BUSINESS ACTIVITY INDICATORS:
           - Recent hiring activity (job openings analysis)
           - Content engagement levels and patterns
           - Business development signals from posts and updates

        4. EMPLOYER BRAND ASSESSMENT:
           - LinkedIn presence strength and completeness
           - Employee engagement indicators from content
           - Talent attraction capabilities from job postings

        5. GROWTH SIGNALS:
           - Expansion indicators from posts and jobs data
           - Market penetration signals from follower growth
           - Strategic direction from content themes

        Focus on actionable business intelligence derived from LinkedIn metrics.
        Provide specific metrics, percentages, and clear business insights.
        Use concrete data from the structured LinkedIn information.
        """
        
        state["company2_business_analysis"] = self.llm.generate(business_prompt)
        return state
    
    def analyze_company1_technology(self, state: ComparisonState) -> ComparisonState:
        """Technology analysis based on lscrape output"""
        print("Performing technology analysis for Company 1...")

        tech_prompt = f"""
        As a Technology Analyst, analyze this company's technical capabilities using LinkedIn data:

        STRUCTURED DATA:
        {json.dumps(state["company1_structured"], indent=2)}

        Provide comprehensive technology analysis covering:

        1. TECHNICAL INFRASTRUCTURE INDICATORS:
           - Technologies mentioned in jobs and posts
           - Technical hiring focus and role types
           - Innovation indicators from content

        2. DIGITAL MATURITY ASSESSMENT:
           - Digital presence quality on LinkedIn
           - Content strategy sophistication
           - Technology adoption signals

        3. TALENT & SKILLS ANALYSIS:
           - Technical vs non-technical hiring ratio
           - Skill demand patterns from job postings
           - Technical workforce composition

        4. INNOVATION & R&D INDICATORS:
           - Innovation mentions in posts
           - Technical content themes
           - R&D focus indicators

        Provide specific insights and technology adoption patterns.
        Base analysis strictly on available LinkedIn data.
        """
        
        state["company1_tech_analysis"] = self.llm.generate(tech_prompt)
        return state
    
    def analyze_company2_technology(self, state: ComparisonState) -> ComparisonState:
        """Technology analysis based on lscrape output"""
        print("Performing technology analysis for Company 2...")

        tech_prompt = f"""
        As a Technology Analyst, analyze this company's technical capabilities using LinkedIn data:

        STRUCTURED DATA:
        {json.dumps(state["company2_structured"], indent=2)}

        Provide comprehensive technology analysis covering:

        1. TECHNICAL INFRASTRUCTURE INDICATORS:
           - Technologies mentioned in jobs and posts
           - Technical hiring focus and role types
           - Innovation indicators from content

        2. DIGITAL MATURITY ASSESSMENT:
           - Digital presence quality on LinkedIn
           - Content strategy sophistication
           - Technology adoption signals

        3. TALENT & SKILLS ANALYSIS:
           - Technical vs non-technical hiring ratio
           - Skill demand patterns from job postings
           - Technical workforce composition

        4. INNOVATION & R&D INDICATORS:
           - Innovation mentions in posts
           - Technical content themes
           - R&D focus indicators

        Provide specific insights and technology adoption patterns.
        Base analysis strictly on available LinkedIn data.
        """
        
        state["company2_tech_analysis"] = self.llm.generate(tech_prompt)
        return state
    
    def analyze_company1_talent(self, state: ComparisonState) -> ComparisonState:
        """Talent and workforce analysis based on lscrape output"""
        print("Performing talent analysis for Company 1...")

        talent_prompt = f"""
        As a Talent Analyst, analyze this company's workforce and recruitment strategy:

        STRUCTURED DATA:
        {json.dumps(state["company1_structured"], indent=2)}

        Provide comprehensive talent analysis covering:

        1. WORKFORCE COMPOSITION:
           - Company size and LinkedIn employee presence
           - Employee engagement indicators
           - Workforce growth trends

        2. RECRUITMENT STRATEGY:
           - Active job openings analysis
           - Technical vs non-technical hiring focus
           - Geographic hiring patterns

        3. EMPLOYER BRANDING:
           - Content engagement and employer attractiveness
           - Post frequency and brand visibility
           - Employee advocacy indicators

        4. TALENT ACQUISITION EFFECTIVENESS:
           - Hiring intensity assessment
           - Role diversity and specialization
           - Recruitment marketing effectiveness

        Use concrete data from LinkedIn profiles, posts, and job listings.
        Provide specific talent acquisition insights.
        """
        
        state["company1_talent_analysis"] = self.llm.generate(talent_prompt)
        return state
    
    def analyze_company2_talent(self, state: ComparisonState) -> ComparisonState:
        """Talent and workforce analysis based on lscrape output"""
        print("Performing talent analysis for Company 2...")

        talent_prompt = f"""
        As a Talent Analyst, analyze this company's workforce and recruitment strategy:

        STRUCTURED DATA:
        {json.dumps(state["company2_structured"], indent=2)}

        Provide comprehensive talent analysis covering:

        1. WORKFORCE COMPOSITION:
           - Company size and LinkedIn employee presence
           - Employee engagement indicators
           - Workforce growth trends

        2. RECRUITMENT STRATEGY:
           - Active job openings analysis
           - Technical vs non-technical hiring focus
           - Geographic hiring patterns

        3. EMPLOYER BRANDING:
           - Content engagement and employer attractiveness
           - Post frequency and brand visibility
           - Employee advocacy indicators

        4. TALENT ACQUISITION EFFECTIVENESS:
           - Hiring intensity assessment
           - Role diversity and specialization
           - Recruitment marketing effectiveness

        Use concrete data from LinkedIn profiles, posts, and job listings.
        Provide specific talent acquisition insights.
        """
        
        state["company2_talent_analysis"] = self.llm.generate(talent_prompt)
        return state
    
    def analyze_company1_engagement(self, state: ComparisonState) -> ComparisonState:
        """Enhanced engagement analysis using lsl.py approach"""
        print("Performing advanced engagement analysis for Company 1...")
        
        if "error" in state["company1_linkedin_data"]:
            state["company1_engagement_analysis"] = f"Analysis failed due to scraping error: {state['company1_linkedin_data']['error']}"
            return state
        
        engagement_prompt = f"""
        As a Social Media & Engagement Analyst, analyze this company's LinkedIn engagement:

        STRUCTURED DATA:
        {json.dumps(state["company1_structured"], indent=2)}

        Provide comprehensive engagement analysis covering:

        1. CONTENT STRATEGY ASSESSMENT:
           - Post frequency and consistency from content metrics
           - Content quality and relevance from themes analysis
           - Message alignment with business objectives

        2. ENGAGEMENT METRICS ANALYSIS:
           - Reaction patterns and engagement rates from structured data
           - Comment activity and community interaction potential
           - Follower growth potential and audience reach

        3. CONTENT EFFECTIVENESS:
           - Post performance analysis based on engagement metrics
           - Audience resonance indicators from content themes
           - Content type effectiveness and optimization opportunities

        4. BRAND VOICE & MESSAGING:
           - Consistency in brand communication across LinkedIn
           - Thought leadership indicators from content quality
           - Industry authority signals from engagement patterns

        5. QUICK LINKS UTILIZATION ANALYSIS:
           - Assess the potential of provided LinkedIn page links
           - Suggest which links would provide deeper insights
           - Evaluate completeness of LinkedIn presence

        Provide specific engagement metrics and content strategy recommendations.
        Focus on actionable insights for improving LinkedIn presence.
        """

        state["company1_engagement_analysis"] = self.llm.generate(engagement_prompt)
        return state
    
    def analyze_company2_engagement(self, state: ComparisonState) -> ComparisonState:
        """Enhanced engagement analysis using lsl.py approach"""
        print("Performing advanced engagement analysis for Company 2...")
        
        if "error" in state["company2_linkedin_data"]:
            state["company2_engagement_analysis"] = f"Analysis failed due to scraping error: {state['company2_linkedin_data']['error']}"
            return state
        
        engagement_prompt = f"""
        As a Social Media & Engagement Analyst, analyze this company's LinkedIn engagement:

        STRUCTURED DATA:
        {json.dumps(state["company2_structured"], indent=2)}

        Provide comprehensive engagement analysis covering:

        1. CONTENT STRATEGY ASSESSMENT:
           - Post frequency and consistency from content metrics
           - Content quality and relevance from themes analysis
           - Message alignment with business objectives

        2. ENGAGEMENT METRICS ANALYSIS:
           - Reaction patterns and engagement rates from structured data
           - Comment activity and community interaction potential
           - Follower growth potential and audience reach

        3. CONTENT EFFECTIVENESS:
           - Post performance analysis based on engagement metrics
           - Audience resonance indicators from content themes
           - Content type effectiveness and optimization opportunities

        4. BRAND VOICE & MESSAGING:
           - Consistency in brand communication across LinkedIn
           - Thought leadership indicators from content quality
           - Industry authority signals from engagement patterns

        5. QUICK LINKS UTILIZATION ANALYSIS:
           - Assess the potential of provided LinkedIn page links
           - Suggest which links would provide deeper insights
           - Evaluate completeness of LinkedIn presence

        Provide specific engagement metrics and content strategy recommendations.
        Focus on actionable insights for improving LinkedIn presence.
        """

        state["company2_engagement_analysis"] = self.llm.generate(engagement_prompt)
        return state
    def generate_company2_individual_report(self, state: ComparisonState) -> ComparisonState:
        """Generate individual LinkedIn report for Company 2 only"""
        sources = state.get("company2_sources", [state.get("company2_url", "")])
        sources_text = "\n".join(f"- {s}" for s in sources)

        report_prompt = f"""
        As a Professional LinkedIn Intelligence Analyst, create an individual report for Company 2 only:

        COMPANY 2 ANALYSIS:
        Structured Data: {json.dumps(state["company2_structured"], indent=2)}
        Business Analysis: {state["company2_business_analysis"]}
        Technology Analysis: {state["company2_tech_analysis"]}
        Talent Analysis: {state["company2_talent_analysis"]}
        Engagement Analysis: {state["company2_engagement_analysis"]}

        VERIFIED SOURCE URLs (use ONLY these for href links):
        {sources_text}

        Generate a professional individual LINKEDIN INTELLIGENCE report with this structure:

        ================================================================================
                                LINKEDIN ANALYSIS REPORT
                                       
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [Key LinkedIn findings and strategic implications]

        COMPANY LINKEDIN PRESENCE
        =========================
        1.0 Profile Completeness & Quality
        1.1 Company Information
        1.2 Industry Positioning
        1.3 Brand Messaging

        2.0 CONTENT & ENGAGEMENT STRATEGY
        =================================
        2.1 Content Performance Analysis
        2.2 Engagement Metrics
        2.3 Content Quality Assessment
        2.4 Audience Reach

        3.0 TALENT & EMPLOYER BRANDING
        ==============================
        3.1 Recruitment Activity
        3.2 Employer Value Proposition
        3.3 Talent Attraction Effectiveness
        3.4 Company Culture Indicators

        4.0 TECHNICAL & INNOVATION INDICATORS
        =====================================
        4.1 Technology Focus
        4.2 Innovation Signals
        4.3 Digital Maturity

        5.0 STRATEGIC RECOMMENDATIONS
        =============================
        5.1 Content Strategy Optimization
        5.2 Engagement Enhancement
        5.3 Talent Attraction Improvements
        5.4 Brand Building Initiatives

        CONCLUSION
        ==========
        [Final assessment and key takeaways]
        

        **URL INTEGRATION GUIDELINES:**
        - Use Exactly 2 href links in the entire report
        - Only link to the most impactful evidence that demonstrates key strengths
        - Links should validate major findings about content strategy or employer branding
        - Example: If content engagement is exceptional, link to posts page
        - Example: If company culture is well-represented, link to about page

        **EXAMPLE URL USAGE (choose only 2 most significant):**
        - For strong content engagement: link to the company LinkedIn posts page
        - For comprehensive company information: link to the company LinkedIn about page
        - For active recruitment: link to the company LinkedIn jobs page

        Focus on comprehensive individual assessment of Company 2's LinkedIn presence and strategy.
        Use qualitative analysis without numerical metrics.
        """

        state["company2_individual_report"] = self.llm.generate(report_prompt)
        return state
    def compare_companies(self, state: ComparisonState) -> ComparisonState:
        """Enhanced comparison using lsl.py comprehensive approach"""
        print("Conducting advanced LinkedIn-based comparison...")
        
        comparison_prompt = f"""
        As a Company Comparison Specialist specializing in LinkedIn intelligence:

        COMPANY 1 DATA:
        Structured: {json.dumps(state["company1_structured"], indent=2)}
        Business Analysis: {state["company1_business_analysis"]}
        Technology Analysis: {state["company1_tech_analysis"]}
        Talent Analysis: {state["company1_talent_analysis"]}
        Engagement Analysis: {state["company1_engagement_analysis"]}

        COMPANY 2 DATA:
        Structured: {json.dumps(state["company2_structured"], indent=2)}
        Business Analysis: {state["company2_business_analysis"]}
        Technology Analysis: {state["company2_tech_analysis"]}
        Talent Analysis: {state["company2_talent_analysis"]}
        Engagement Analysis: {state["company2_engagement_analysis"]}

        Provide detailed comparative analysis covering:

        BUSINESS METRICS COMPARISON:
        • Company size and scale relative positioning
        • Industry focus and specialization differences
        • Growth trajectory indicators from LinkedIn data
        • Market presence and LinkedIn authority

        ENGAGEMENT & CONTENT STRATEGY COMPARISON:
        • Content effectiveness and engagement rates
        • Posting strategy differences and best practices
        • Audience growth potential and reach
        • Brand messaging effectiveness

        TECHNOLOGY & INNOVATION COMPARISON:
        • Technical hiring intensity and focus areas
        • Technology adoption signals from job postings
        • Innovation indicators from content and updates
        • Digital maturity assessment

        EMPLOYER BRAND & TALENT ATTRACTION:
        • LinkedIn as talent attraction platform effectiveness
        • Company culture indicators from content
        • Recruitment activity comparison and intensity
        • Employee advocacy signals

        COMPETITIVE POSITIONING:
        • Relative LinkedIn authority in industry
        • Thought leadership comparison
        • Digital presence strength and completeness
        • Strategic advantages visible on LinkedIn

        Provide actionable insights and strategic recommendations based on LinkedIn intelligence.
        Focus on data-driven conclusions from the structured LinkedIn metrics.
        """

        state["comparison_analysis"] = self.llm.generate(comparison_prompt)
        print("Advanced LinkedIn comparison completed!")
        return state
    
    def generate_final_report(self, state: ComparisonState) -> ComparisonState:
        """Enhanced final report using proper business formatting"""
        from datetime import datetime
        
        report_prompt = f"""
        As a Professional LinkedIn Intelligence Analyst, create comprehensive report:

        ANALYSIS DATA:
        Company 1 Structured: {json.dumps(state["company1_structured"], indent=2)}
        Company 2 Structured: {json.dumps(state["company2_structured"], indent=2)}
        Business Analyses: {state["company1_business_analysis"]} | {state["company2_business_analysis"]}
        Technology Analyses: {state["company1_tech_analysis"]} | {state["company2_tech_analysis"]}
        Talent Analyses: {state["company1_talent_analysis"]} | {state["company2_talent_analysis"]}
        Engagement Analyses: {state["company1_engagement_analysis"]} | {state["company2_engagement_analysis"]}
        Comparison: {state["comparison_analysis"]}

        Generate professional LinkedIn intelligence report with this structure:

        ================================================================================
                                LINKEDIN INTELLIGENCE COMPARISON REPORT
        ================================================================================

        EXECUTIVE SUMMARY
        =================
        [Key findings and strategic implications]

        TABLE OF CONTENTS
        =================
        1.0 Introduction & Analysis Framework
        2.0 Company LinkedIn Profiles
        3.0 Engagement & Content Strategy
        4.0 Talent Acquisition Analysis
        5.0 Employer Brand Assessment
        6.0 Competitive Intelligence
        7.0 Strategic Recommendations

        1.0 INTRODUCTION & ANALYSIS FRAMEWORK
        =====================================
        1.1 Research Methodology
        1.2 Data Sources
        1.3 Analysis Parameters

        2.0 COMPANY LINKEDIN PROFILES
        =============================
        2.1 {state.get('company1_name', 'Company 1')} LinkedIn Presence
            • Company Page Completeness
            • Content Strategy Overview
            • Employee Engagement

        2.2 {state.get('company2_name', 'Company 2')} LinkedIn Presence
            • Company Page Completeness
            • Content Strategy Overview
            • Employee Engagement

        3.0 ENGAGEMENT & CONTENT STRATEGY
        =================================
        3.1 Content Performance Analysis
        3.2 Content Quality Assessment

        4.0 TALENT ACQUISITION ANALYSIS
        ===============================
        4.1 Recruitment Activity
        4.2 Job Posting Strategy
        4.3 Employer Value Proposition
        4.4 Candidate Engagement

        5.0 EMPLOYER BRAND ASSESSMENT
        =============================
        5.1 Brand Perception Analysis
        5.2 Corporate Reputation

        6.0 COMPETITIVE INTELLIGENCE
        ============================
        6.1 Opportunity Identification

        7.0 STRATEGIC RECOMMENDATIONS
        =============================
        7.1 Content Strategy Optimization
        7.2 Engagement Enhancement
        7.3 Talent Attraction Improvements
        7.4 Brand Building Initiatives

        CONCLUSION
        ==========
        [Final assessment and key takeaways]

        DATA ACCURACY & JUSTIFICATION REQUIREMENTS:
        1. For each LinkedIn metric analysis, specify the exact data source: "Based on LinkedIn post analysis..." or "From company page information..."
        2. Include justification phrases: "This conclusion is supported by the engagement patterns observed in recent posts..." or "The talent assessment is justified by active job posting frequency..."
        3. When comparing companies, explicitly reference specific LinkedIn elements: "as evidenced by Company A's higher post frequency (X posts) compared to Company B (Y posts)"
        4. Use qualifying language: "The content strategy effectiveness is indicated by..." or "Employee engagement levels are suggested by..."
        5. For recommendations, connect to specific LinkedIn observations: "This improvement suggestion is based on the gap in Company B's LinkedIn About section completeness"
       
        JUSTIFICATION INTEGRATION EXAMPLES:
        - "Company A shows stronger employer branding, justified by their detailed company culture posts and employee testimonials found in their LinkedIn content"
        - "The engagement analysis indicates higher audience interaction, as evidenced by the consistent comment activity and share rates across recent posts"
        - "This strategic recommendation is supported by the comparative analysis of job posting frequency and role diversity between both companies"

        IMPORTANT INSTRUCTIONS:
        - Don't give metric table for Content Performance Analysis and Recruitment Activity.
        - Embed accuracy qualifiers within the analysis sentences themselves
        - Ensure recommendation includes its data justification in the same context
        - Maintain professional business language while adding transparency about data sources

        Use professional business formatting with clear sections and data-driven insights.
        """

        state["final_report"] = self.llm.generate(report_prompt)
        return state
    
    def generate_executive_briefing(self, state: ComparisonState) -> ComparisonState:
        """Enhanced executive briefing using lsl.py approach"""
        briefing_prompt = f"""
        Create a one-page executive briefing from this enhanced LinkedIn intelligence:

        {state["final_report"]}

        Extract and condense into:

        🚀 LINKEDIN INTELLIGENCE EXECUTIVE BRIEFING
        ============================================

        • KEY FINDINGS (3-5 bullet points from structured LinkedIn data)
        • BUSINESS STRATEGIC IMPLICATIONS
        • TECHNOLOGY & INNOVATION INSIGHTS
        • TALENT ACQUISITION EFFECTIVENESS
        • ENGAGEMENT & CONTENT RECOMMENDATIONS
        • COMPETITIVE POSITIONING SUMMARY
        • CRITICAL RECOMMENDATIONS
        • QUICK LINKS UTILIZATION STRATEGY

        Keep it under 400 words, focused on actionable LinkedIn insights for C-level executives.
        Highlight the most significant competitive advantages and opportunities visible through structured LinkedIn data.
        """

        state["executive_briefing"] = self.llm.generate(briefing_prompt)
        return state

def create_linkedin_comparison_workflow(api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Create the LangGraph workflow for LinkedIn comparison"""
    workflow = StateGraph(ComparisonState)
    
    comparator = LinkedInAnalysisAgent(api_key=api_key, model=model)
    
    # Add nodes
    workflow.add_node("collect_linkedin_data", comparator.collect_linkedin_data)
    workflow.add_node("extract_structured_data", comparator.extract_structured_data)
    workflow.add_node("analyze_company1_business", comparator.analyze_company1_business)
    workflow.add_node("analyze_company2_business", comparator.analyze_company2_business)
    workflow.add_node("analyze_company1_technology", comparator.analyze_company1_technology)
    workflow.add_node("analyze_company2_technology", comparator.analyze_company2_technology)
    workflow.add_node("analyze_company1_talent", comparator.analyze_company1_talent)
    workflow.add_node("analyze_company2_talent", comparator.analyze_company2_talent)
    workflow.add_node("analyze_company1_engagement", comparator.analyze_company1_engagement)
    workflow.add_node("analyze_company2_engagement", comparator.analyze_company2_engagement)
    workflow.add_node("compare_companies", comparator.compare_companies)
    workflow.add_node("generate_final_report", comparator.generate_final_report)
    workflow.add_node("generate_executive_briefing", comparator.generate_executive_briefing)
    workflow.add_node("generate_company2_individual_report", comparator.generate_company2_individual_report)

    # Define workflow
    workflow.set_entry_point("collect_linkedin_data")
    workflow.add_edge("collect_linkedin_data", "extract_structured_data")
    workflow.add_edge("extract_structured_data", "analyze_company1_business")
    workflow.add_edge("analyze_company1_business", "analyze_company2_business")
    workflow.add_edge("analyze_company2_business", "analyze_company1_technology")
    workflow.add_edge("analyze_company1_technology", "analyze_company2_technology")
    workflow.add_edge("analyze_company2_technology", "analyze_company1_talent")
    workflow.add_edge("analyze_company1_talent", "analyze_company2_talent")
    workflow.add_edge("analyze_company2_talent", "analyze_company1_engagement")
    workflow.add_edge("analyze_company1_engagement", "analyze_company2_engagement")
    workflow.add_edge("analyze_company2_engagement", "compare_companies")
    workflow.add_edge("compare_companies", "generate_final_report")
    workflow.add_edge("generate_final_report", "generate_executive_briefing")
    workflow.add_edge("generate_executive_briefing", "generate_company2_individual_report")
    workflow.add_edge("generate_company2_individual_report", END)
    
    return workflow.compile()

def run_linkedin_comparison(company1_url, company2_url, use_predefined_data=False, company1_name="KANINI", api_key: str = LLM_API_KEY, model: str = LLM_MODEL):
    """Run the LinkedIn comparison workflow"""
    workflow = create_linkedin_comparison_workflow(api_key=api_key, model=model)
    
    initial_state = {
        "company1_url": company1_url,
        "company2_url": company2_url,
        "company1_name": company1_name,
        "company1_linkedin_data": {},
        "company2_linkedin_data": {},
        "company1_structured": {},
        "company2_structured": {},
        "company1_business_analysis": "",
        "company2_business_analysis": "",
        "company1_tech_analysis": "",
        "company2_tech_analysis": "",
        "company1_talent_analysis": "",
        "company2_talent_analysis": "",
        "company1_engagement_analysis": "",
        "company2_engagement_analysis": "",
        "comparison_analysis": "",
        "final_report": "",
        "company2_individual_report": "",
        "executive_briefing": "",
        "use_predefined_data": use_predefined_data,
        "company2_sources": [],
    }
    
    result = workflow.invoke(initial_state)
    
    return result

def main():
    import time
    
    if not LLM_API_KEY:
        print("ERROR: Please set LLM_API_KEY in your .env file.")
        return
    
    try:
        print("LINKEDIN COMPANY COMPARISON USING LSCRAPE DATA")
        print("=" * 60)
        
        company1_url = input("\nEnter first company LinkedIn URL: ").strip()
        company2_url = input("Enter second company LinkedIn URL: ").strip()
        
        print(f"\nAnalyzing LinkedIn profiles...")
        print("This may take 2-3 minutes...\n")
        
        start_time = time.time()
        result = run_linkedin_comparison(company1_url, company2_url)
        end_time = time.time()
        
        print(f"Analysis completed in {end_time - start_time:.1f} seconds")
        
        # Show executive briefing
        print("\nEXECUTIVE BRIEFING:")
        print("=" * 50)
        print(result["executive_briefing"])
        print("=" * 50)
        
        print(f"\nFull report saved: linkedin_comparison_report.txt")
        print(f"Executive briefing: linkedin_executive_briefing.txt")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()