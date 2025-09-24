from crewai import Task

from .agents import (
    url_scrapper, 
    url_analyzer, 
    pdf_analyzer, 
    financial_report_generator, 
    linkedin_agent,
    company_researcher,
    competitor_analyst,
    finance_analyst,
    market_analyst,
    news_gatherer
)

# --- Sales Intelligence Tasks ---

company_task = Task(
    description="Research '{company_name}' for a detailed overview: founding, industry, offerings, size, and executives.",
    expected_output="A markdown report with a comprehensive company profile.",
    agent=company_researcher,
)

competitor_task = Task(
    description="Analyze the top 3-5 competitors for '{company_name}', detailing their market position, strengths, and weaknesses.",
    expected_output="A markdown report detailing the competitive landscape.",
    agent=competitor_analyst,
)

finance_task = Task(
    description="Conduct a financial analysis of '{company_name}', adapting for public (using FMP/EDGAR) or private (using web search) status.",
    expected_output="A detailed financial summary in markdown.",
    agent=finance_analyst,
)

market_task = Task(
    description="Analyze the market for '{company_name}', including size, CAGR, trends, and opportunities.",
    expected_output="A structured market analysis report in markdown.",
    agent=market_analyst,
)

news_task = Task(
    description="Gather and summarize the top 3-5 recent news articles for '{company_name}', including sentiment and business impact.",
    expected_output="A bulleted list of recent news summaries in markdown.",
    agent=news_gatherer,
)

# --- IT & Financial Analysis Tasks (Corrected Workflow) ---

url_scrape_task = Task(
    description=(
        "Thoroughly scrape the company website {url} to gather information on its business and strategy. "
        "Crucially, identify the official name of the company from the website content."
    ),
    expected_output=(
        "A detailed report on the company's performance and strategy, which MUST include a final line with the official company name. "
        "Example: 'Official Company Name: Monogram Health'"
    ),
    agent=url_scrapper,
)

# Corrected: This task is now split into two for reliability
find_linkedin_profile_task = Task(
    description=(
        "You will be given context containing an official company name. "
        "Your ONLY job is to use your search tool with the query '[Official Company Name] LinkedIn page' to find their official LinkedIn company URL. "
        "From this URL (e.g., 'https://www.linkedin.com/company/monogram-health'), you must extract and return ONLY the unique 'universal name' (e.g., 'monogram-health')."
    ),
    expected_output=(
        "A single string containing only the LinkedIn universal name. For example: 'monogram-health'"
    ),
    agent=linkedin_agent,
    context=[url_scrape_task],
)

analyze_linkedin_profile_task = Task(
    description=(
        "You will be given context containing a LinkedIn universal name. "
        "Use the `linkedin_insights_tool` with this exact universal name to fetch the company's data. "
        "Then, provide a comprehensive summary of the insights found in the JSON response."
    ),
    expected_output=(
        "A markdown summary of the company's LinkedIn profile and recent post activity, based on the data retrieved."
    ),
    agent=linkedin_agent,
    context=[find_linkedin_profile_task], 
)

url_analyze_task = Task(
    description=(
        "Synthesize the scraped web content (from the first task) AND the LinkedIn analysis (from the third task) into a single, comprehensive report. "
        "Your report must integrate insights from both sources to provide a cohesive strategic analysis."
    ),
    expected_output="A single, cohesive markdown report that combines web and LinkedIn insights into a final strategic analysis.",
    agent=url_analyzer,
    context=[url_scrape_task, analyze_linkedin_profile_task],
)


# Other tasks
pdf_reading_task = Task(
    description="Extract all text from the PDF at {pdf_path}.",
    expected_output="A string containing all extracted PDF text.",
    agent=pdf_analyzer,
)

pdf_analyze_task = Task(
    description="Analyze the text from the PDF at {pdf_path}, identify the company name, and supplement with web research to create a full technology report.",
    expected_output="A detailed technology-focused report based on the PDF content and web research.",
    agent=pdf_analyzer,
)

generate_financial_task = Task(
    description="Synthesize all provided research (company, competitor, market, news) for '{company_name}' into a final, context-aware financial report.",
    expected_output="A comprehensive financial report in markdown, integrating all research context.",
    agent=financial_report_generator,
    context=[company_task, competitor_task, finance_task, market_task, news_task],
)



#-------------------------------------------------------------------------------------------------
# from crewai import Task, Crew, Process
# from BizAgent.agents.agents import url_scrapper, url_analyzer, pdf_analyzer, financial_report_generator, linkedin_agent
# from crewai import Task
# from BizAgent.tools.tools import  web_scraping_tool,search_tool,fetch_pdf_content, linkedin_insights_tool


# # Scraping Tasks
# url_scrape_task = Task(
#     description="""Thoroughly scrape the company website {url} and search in browser with the  help of company name scrap the necessary information from those links to get necessary information, focusing on:
#     1. Strong performing areas
#     2. Areas where the company faced challenges   
#     3. Strategic focus areas for the future
#     4. Details on software solutions and recurring revenue
#     5. Regional performance and key markets
#     6. Specific segments like Enterprise and Long-Term Care (LTC)
#     7. financial report for current year""",
#     expected_output="""A detailed report containing:
#     1. Overview of the company's strong performing areas
#     2. Summary of the challenges faced by the company
#     3. List of strategic focus areas for the future
#     4. Insights into the company's software solutions and recurring revenue growth
#     5. Analysis of regional performance and key markets
#     6. Breakdown of performance in specific segments like Enterprise and Long-Term Care (LTC)
#     7. financial report for current year""",
#     tools=[web_scraping_tool,search_tool],
#     agent=url_scrapper
# )

# # Analyzing Task
# url_analyze_task = Task(
#     description="""Analyze the scraped content from {url} to create a comprehensive technology-focused report.use company name to search news and financial report related to it and extract necessary information to generate :
#     1. Identify the specific technologies and tools the company is currently using across different areas of their operations.
#     2. Determine the company's technological strengths, highlighting areas where they seem to be performing well or innovating.
#     3. Uncover any technological weaknesses or gaps in their current stack.
#     4. Assess the company's technological maturity and identify their focus areas for future technology development or adoption.
#     5. Propose potential IT services or technologies that could address the company's needs, enhance their capabilities, or help them overcome identified challenges.
#     6. Summary of financial data like profit percentage etc for current year
#     7. Latest news about the company """,

#     expected_output="""A detailed technology-focused report including:
#     1. Company overview with insights into their technological positioning and digital maturity.
#     2. Comprehensive analysis of the company's current technology stack, including:
#        - Specific technologies and tools used in different operational areas
#        - How these technologies are being applied
#        - Any unique or innovative uses of technology
#     3. Technology-based SWOT analysis:
#        - Technological strengths: Areas where the company excels in tech usage or innovation
#        - Technological weaknesses: Gaps or outdated systems in their current stack
#        - Opportunities: Potential areas for technological improvement or adoption
#        - Threats: Potential risks or challenges related to their current technology usage
#     4. Analysis of the company's strong performing areas in terms of technology over the past year.
#     5. Identified areas of struggle or challenges related to technology implementation or usage.
#     6. The company's apparent focus areas for future technological development or adoption.
#     7. Specific recommendations for IT services or technologies that your company could provide, including:
#        - How these services align with the client's technological needs and future focus
#        - The potential impact of these services on the client's technological capabilities and business operations
#        - A strategy for approaching the company with these technology-focused service offerings
#     8. Any additional insights or observations about the company's overall technological strategy or digital transformation efforts.
#     9. financial report for current year just a rough figure 
#     10.latest News about the company just headlines not any links search in internet or collect information from the scrapped website data use the tool""",
#     tools = [search_tool],
#     agent=url_analyzer,
#     depends_on=url_scrape_task,
#     output_file="url_service_opportunity.md"
# )



# url_final_report_task = Task(
#     description="Generate a final report by combining the outputs of the URL scraping and analysis tasks.",
#     expected_output="A comprehensive final report that includes the results from both the URL scraping and analysis tasks.",
#     agent=url_analyzer,
#     depends_on=[url_scrape_task, url_analyze_task],
#     output_file="final_report.md")




# pdf_reading_task = Task(
#         description="Get the content from the PDF {pdf_url} ",
#         agent=pdf_analyzer,
#         expected_output="content extracted from the pdf",
#         tools = [fetch_pdf_content],
# )


# pdf_analyze_task = Task(
#     description="""Analyze the extracted content  from pdf {pdf_url} to create a comprehensive technology-focused report.use company name to search news and financial report related to it and extract necessary information to generate :
#     1. Identify the specific technologies and tools the company is currently using across different areas of their operations.
#     2. Determine the company's technological strengths, highlighting areas where they seem to be performing well or innovating.
#     3. Uncover any technological weaknesses or gaps in their current stack.
#     4. Assess the company's technological maturity and identify their focus areas for future technology development or adoption.
#     5. Propose potential IT services or technologies that could address the company's needs, enhance their capabilities, or help them overcome identified challenges.
#     6. Summary of financial data like profit percentage etc for current year
#     7. Latest news about the company """,
    
#     expected_output="""A detailed technology-focused report including:
#     1. Company overview with insights into their technological positioning and digital maturity.
#     2. Comprehensive analysis of the company's current technology stack, including:
#        - Specific technologies and tools used in different operational areas
#        - How these technologies are being applied
#        - Any unique or innovative uses of technology
#     3. Technology-based SWOT analysis:
#        - Technological strengths: Areas where the company excels in tech usage or innovation
#        - Technological weaknesses: Gaps or outdated systems in their current stack
#        - Opportunities: Potential areas for technological improvement or adoption
#        - Threats: Potential risks or challenges related to their current technology usage
#     4. Analysis of the company's strong performing areas in terms of technology over the past year.
#     5. Identified areas of struggle or challenges related to technology implementation or usage.
#     6. The company's apparent focus areas for future technological development or adoption.
#     7. Specific recommendations for IT services or technologies that your company could provide, including:
#        - How these services align with the client's technological needs and future focus
#        - The potential impact of these services on the client's technological capabilities and business operations
#        - A strategy for approaching the company with these technology-focused service offerings
#     8. Any additional insights or observations about the company's overall technological strategy or digital transformation efforts.
#     9. financial report for latest year  detailed report or information available  
#     10.latest News about the company just headlines not any links""",
    
#     agent=pdf_analyzer,
#     tools = [search_tool],
#     output_file="pdf_service_opportunity.md"
# )

# generate_financial_task = Task(
#     description="""
#         Use the tool provided to generate a comprehensive financial report 
#         in markdown format using the provided company name.
#     """,
#     expected_output="Markdown report saved at media/financial_report.md",
#     agent=financial_report_generator,
#     async_execution=False,
#     output_file="media/financial_report.md"
# )

# linkedin_task = Task(
#     description="Fetch LinkedIn insights for {universal_name} using the tool. Return clean JSON only.",
#     expected_output="Valid JSON with company_analysis, posts_analysis, activity_summary, sales_signals.",
#     tools=[linkedin_insights_tool],
#     agent=linkedin_agent,
#     output_file="media/linkedin_insights.json"  # better as .json
# )
