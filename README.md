# BizzAnalyzer

A full-stack Business Intelligence platform that compares two companies side-by-side using data scraped from their websites, LinkedIn profiles, and financial sources. AI agents analyze each data source independently and a unified report is generated combining all three perspectives.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Backend](#backend)
  - [API Endpoints](#api-endpoints)
  - [Agents](#agents)
  - [Scrapers](#scrapers)
  - [Services](#services)
  - [LLM Support](#llm-support)
- [Frontend](#frontend)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Demo Mode](#demo-mode)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)

---

## Overview

BizzAnalyzer takes two company names and their associated URLs as input, runs a multi-agent AI analysis pipeline across three data dimensions (website, LinkedIn, financial), and produces:

- A unified 2-page comparison report (Word document)
- Individual reports for Company 2 across all three dimensions
- An executive summary
- Leadership/executive profiles for both companies
- Downloadable `.docx` files for each report type

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| AI Orchestration | LangGraph (StateGraph) |
| LLM Providers | Google Gemini / OpenAI / Groq (via native SDKs) |
| Web Scraping | BeautifulSoup4, Requests |
| LinkedIn Scraping | BeautifulSoup4 (direct HTTP) |
| Financial Data | Yahoo Finance API, Alpha Vantage, DuckDuckGo search |
| LinkedIn URL Resolution | DuckDuckGo Search (LangChain community tool) |
| Leader Extraction | Groq (llama-3.3-70b) |
| Document Generation | python-docx |
| Environment | python-dotenv |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React (Vite) |
| Routing | React Router |
| HTTP | Fetch API |
| Styling | CSS Modules |

---

## Project Structure

```
BizzAnalyzer/
├── .env                          # Environment variables (API keys)
├── requirements.txt              # Python dependencies
│
├── backend/
│   ├── main.py                   # FastAPI app entry point, CORS setup
│   ├── pytest.ini
│   ├── reports/                  # Generated .docx files stored here
│   ├── data/
│   │   └── companies.json        # Kanini partner companies list
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # All API endpoints + background task runner
│   │   │
│   │   ├── agents/
│   │   │   ├── website_agent.py  # Website scrape + LLM analysis workflow
│   │   │   ├── linkedin_agent.py # LinkedIn scrape + LLM analysis workflow
│   │   │   └── financial_agent.py# Financial scrape + LLM analysis workflow
│   │   │
│   │   ├── core/
│   │   │   ├── config.py         # Loads and validates all env variables
│   │   │   ├── llm_client.py     # Universal LLM client (Gemini/OpenAI/Groq)
│   │   │   └── prompts.py        # Shared prompt templates
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic request/response models
│   │   │
│   │   ├── scrapers/
│   │   │   ├── website_scraper.py    # Scrapes company websites
│   │   │   ├── linkedin_scraper.py   # Scrapes LinkedIn company pages
│   │   │   └── financial_scraper.py  # Fetches financial data
│   │   │
│   │   ├── services/
│   │   │   ├── comparison_workflow.py  # Unified orchestrator + docx generation
│   │   │   ├── leader_search.py        # Leader LinkedIn URL enrichment
│   │   │   └── linkedin_resolver.py    # Resolves company LinkedIn URLs
│   │   │
│   │   └── leader_extraction/
│   │       ├── extractor.py      # Main leader extraction pipeline
│   │       ├── llm_extractor.py  # Groq LLM call for executive extraction
│   │       ├── scraper.py        # Scrapes company pages for leader text
│   │       └── verifier.py       # Verifies extracted leader names
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_agent_integration.py
│       ├── test_backend_integration.py
│       ├── test_complete_analysis.py
│       ├── test_financial_agent.py
│       ├── test_linkedin_agent.py
│       └── test_website_agent.py
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── constants/
        │   └── index.js           # COMPANY_FIELDS config
        ├── hooks/
        │   ├── useComparisonForm.js    # Form state, validation, polling
        │   └── useLinkedinResolver.js  # LinkedIn URL auto-resolve hook
        ├── pages/
        │   ├── ComparisonPage.jsx  # Input form + terminal progress
        │   └── ResultsPage.jsx     # Results display + download controls
        ├── components/
        │   ├── Navbar.jsx
        │   └── PreviewModal.jsx    # Modal to preview report text
        └── styles/
            ├── base.css
            ├── buttons.css
            ├── tokens.css
            └── responsive.css
```

---

## Architecture

```
User (Browser)
     |
     | POST /run-comparison
     v
FastAPI (routes.py)
     |
     | BackgroundTask
     v
run_analysis_in_background()
     |
     v
run_unified_comparison()  <-- comparison_workflow.py
     |
     |--- run_website_analysis()
     |         |
     |         v
     |    LangGraph: website_agent.py
     |    [scrape → extract → analyze → compare → report]
     |
     |--- run_linkedin_analysis()
     |         |
     |         v
     |    LangGraph: linkedin_agent.py
     |    [scrape → structure → analyze → compare → report]
     |
     |--- run_financial_analysis()
     |         |
     |         v
     |    LangGraph: financial_agent.py
     |    [fetch data → calculate ratios → analyze → compare → report]
     |
     v
generate_final_unified_report()
     |
     v
create_professional_word_document()  → saves .docx to reports/
     |
     v
process_browser_style_search()  → leader extraction
     |
     v
Session updated: status = "completed"
     |
     | GET /analysis-status/:session_id  (polled every 1s by frontend)
     v
Frontend navigates to /results/:sessionId
```

---

## Backend

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/run-comparison` | Starts background analysis, returns `session_id` |
| GET | `/analysis-status/{session_id}` | Returns status, reports, leaders |
| GET | `/terminal-output/{session_id}` | Returns incremental terminal log lines |
| GET | `/download-report/{session_id}/{report_type}` | Downloads `.docx` file |
| POST | `/resolve-linkedin-url` | Resolves a company name to LinkedIn URL |
| GET | `/cleanup-sessions` | Removes sessions older than 1 hour |
| GET | `/health` | Health check |

**Report types for download:** `full`, `website`, `linkedin`, `financial`

**ComparisonRequest body:**
```json
{
  "company1_name": "KANINI",
  "company2_name": "TCS",
  "company1_website": "https://kanini.com",
  "company2_website": "https://tcs.com",
  "company1_linkedin": "https://www.linkedin.com/company/kanini",
  "company2_linkedin": "https://www.linkedin.com/company/tata-consultancy-services",
  "use_predefined_data": true,
  "api_key": "optional-override-key",
  "model": "optional-model-name"
}
```

---

### Agents

Each agent is a LangGraph `StateGraph` — a directed graph where each node is a function that reads from and writes to a shared state dictionary.

#### `website_agent.py` — `LangGraphCompanyComparator`

**Graph nodes (in order):**
1. `scrape_data` — Scrapes both company websites using `WebsiteScraper`
2. `extract_structured_data` — LLM extracts JSON (services, tech stack, business model, etc.)
3. `analyze_company1_business` — LLM business strategy analysis
4. `analyze_company2_business`
5. `analyze_company1_technology` — LLM tech stack analysis
6. `analyze_company2_technology`
7. `compare_companies` — LLM side-by-side comparison
8. `generate_final_report` — Full website intelligence report
9. `generate_executive_briefing` — Condensed executive summary
10. `generate_company2_individual_report` — Standalone report for Company 2

#### `linkedin_agent.py` — `LinkedInAnalysisAgent`

**Graph nodes (in order):**
1. `collect_linkedin_data` — Scrapes LinkedIn pages using `SimpleLinkedInScraper`
2. `extract_structured_data` — Structures raw scrape into categories
3. `analyze_company1_business` / `analyze_company2_business`
4. `analyze_company1_technology` / `analyze_company2_technology`
5. `analyze_company1_talent` / `analyze_company2_talent`
6. `analyze_company1_engagement` / `analyze_company2_engagement`
7. `compare_companies`
8. `generate_final_report`
9. `generate_executive_briefing`
10. `generate_company2_individual_report`

#### `financial_agent.py` — `FinancialAnalysisAgent`

**Graph nodes (in order):**
1. `collect_financial_data` — Fetches via Yahoo Finance → Alpha Vantage → smart estimates
2. `analyze_company1_financials` / `analyze_company2_financials`
3. `compare_profitability`
4. `compare_liquidity_solvency`
5. `analyze_growth_potential`
6. `generate_investment_recommendation`
7. `generate_final_financial_report`
8. `generate_executive_summary`
9. `generate_company2_individual_report`

---

### Scrapers

#### `website_scraper.py` — `WebsiteScraper`
- Fetches the company homepage with a browser-like User-Agent
- Extracts: company name, meta description, contact info (emails, phones), products/services, about section, key pages, social links, detected technologies (WordPress, React, jQuery, Google Analytics, etc.)
- Visits the contact page and about page separately for richer data
- Returns everything as a formatted text string

#### `linkedin_scraper.py` — `SimpleLinkedInScraper`
- Direct HTTP request to LinkedIn company page (no login)
- Extracts: company name, tagline, followers, overview, about details (industry, size, HQ, founded, specialties), posts (with engagement), jobs, employee count
- Filters out low-quality posts using keyword heuristics
- Generates dynamic page links (posts, people, jobs, about)

#### `financial_scraper.py` — `WorkingFinancialScraper`
- **Priority 1:** Yahoo Finance API — searches by company name, gets market cap, derives revenue/income estimates
- **Priority 2:** Alpha Vantage API — fallback stock data
- **Priority 3:** DuckDuckGo web search — scrapes financial pages
- **Priority 4:** Smart estimates — derives figures from company name characteristics (tech vs consulting vs trading)
- Calculates ratios: gross margin, operating margin, net margin, ROA, ROE, current ratio, debt-to-equity

---

### Services

#### `comparison_workflow.py` — `UnifiedCompanyComparator`
- Runs all three agents sequentially
- Calls `generate_final_unified_report()` which synthesizes all three reports into one 2-page comparison
- Saves 4 Word documents: unified, website, linkedin, financial
- `create_professional_word_document()` — formats content with headings, bullet points, hyperlinks, tables, TOC, and metadata page

#### `linkedin_resolver.py`
- Uses DuckDuckGo search to find a company's LinkedIn URL from just a name
- Cleans URLs (removes `/jobs`, `/about`, `/people` suffixes)
- Scores candidates by name match, slug simplicity, title indicators
- Falls back to direct URL construction if search fails

#### `leader_search.py`
- Enriches verified leaders with LinkedIn profile URLs
- Uses DuckDuckGo to search `"Person Name" "Company" LinkedIn`

---

### LLM Support

`app/core/llm_client.py` — `LLMClient`

Supports multiple providers detected from the API key prefix:

| Key Prefix | Provider | Default Model |
|---|---|---|
| `AIza...` | Google Gemini | `gemini-2.0-flash` |
| `sk-...` | OpenAI | `gpt-4o-mini` |
| `gsk_...` | Groq | `llama-3.3-70b-versatile` |

Uses native SDKs only — no LiteLLM required. Gemini uses `google-generativeai`, OpenAI and Groq use the `openai` SDK (Groq is OpenAI-compatible with a different base URL).

---

## Frontend

### `ComparisonPage.jsx`
- Form with fields for Company 1 and Company 2: name, website, LinkedIn
- LinkedIn field auto-resolves company names to URLs via `/resolve-linkedin-url`
- If Company 1 is "KANINI", shows a toggle to use pre-scraped Kanini data
- On submit, calls `/run-comparison` and starts polling `/terminal-output` every second
- Shows live terminal-style progress log
- Navigates to `/results/:sessionId` when status becomes `completed`

### `ResultsPage.jsx`
- Fetches `/analysis-status/:sessionId` once on load
- Displays executive overview text
- Shows leader cards for both companies (name, role, LinkedIn link, photo)
- Download buttons for each report type (full, website, linkedin, financial)
- Preview button opens `PreviewModal` with raw report text

### `useComparisonForm.js`
- Manages all form state
- Validates required fields
- Handles LinkedIn auto-resolution with debounce
- Runs polling loop with `useEffect` + `setInterval`
- Navigates on completion

---

## Setup & Installation

### Backend

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (see Environment Variables section)

# 4. Start the server
cd backend
uvicorn main:app --reload
```

Server runs at: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at: `http://localhost:5173`

---

## Environment Variables

Create a `.env` file in the project root:

```ini
# -----------------------------------------------
# LLM Provider — pick ONE of the following:
# -----------------------------------------------

# Google Gemini (default)
LLM_API_KEY=AIzaSy...
LLM_MODEL=gemini-2.0-flash

# OpenAI
# LLM_API_KEY=sk-...
# LLM_MODEL=gpt-4o-mini

# Groq
# LLM_API_KEY=gsk_...
# LLM_MODEL=llama-3.3-70b-versatile

# Backward compat — still works if you use this instead of LLM_API_KEY
# GOOGLE_API_KEY=AIzaSy...

# -----------------------------------------------
# Groq — required for leader/executive extraction
# -----------------------------------------------
GROQ_API_KEY=gsk_...

# -----------------------------------------------
# Optional
# -----------------------------------------------
SERPER_API_KEY=...          # Google Search fallback for LinkedIn
ALPHA_VANTAGE_API_KEY=...   # Financial data fallback
```

---

## Usage

1. Start backend and frontend servers
2. Open `http://localhost:5173`
3. Enter Company 1 details (name, website, LinkedIn URL or company name)
4. Enter Company 2 details
5. For quick testing: enter `KANINI` as Company 1 and enable "Use PreScraped Kanini Data"
6. Click "Run Comprehensive Comparison"
7. Watch the live terminal progress log
8. When complete, view the results page:
   - Executive summary
   - Leadership cards
   - Download buttons for all 4 report types
   - Preview any report inline

---

## Demo Mode

If the LLM API returns a quota error (HTTP 429), the system automatically switches to **demo mode**:
- Returns placeholder executive overview and full report text
- Status is set to `demo_mode` instead of `completed`
- Frontend still navigates to results page and shows the demo content

---

## Tests

```bash
cd backend
pip install pytest
pytest -q
```

Test files:
- `test_agent_integration.py` — tests all three agents together
- `test_backend_integration.py` — tests API endpoints
- `test_complete_analysis.py` — end-to-end workflow test
- `test_financial_agent.py` — financial agent unit tests
- `test_linkedin_agent.py` — LinkedIn agent unit tests
- `test_website_agent.py` — website agent unit tests

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `NoneType has no attribute startswith` | `LLM_API_KEY` or `GOOGLE_API_KEY` is missing from `.env` |
| `Invalid URL` on LinkedIn field | Enter full URL like `https://www.linkedin.com/company/name` or just the company name |
| `Failed to start analysis` | Check backend is running at port 8000 and CORS is not blocking |
| `Report file not generated` | Check `reports/` folder and session logs via `/terminal-output/:id` |
| `429 / quota exceeded` | System enters demo mode automatically. Upgrade API plan or switch provider |
| LinkedIn scraping returns empty data | LinkedIn blocks direct scraping. Use predefined data or provide the URL manually |
| Financial data shows estimates | Company is not publicly traded. Scraper falls back to smart estimates |
