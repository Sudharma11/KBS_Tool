
from crewai import Task, Crew, Process
from BizAgent.agents.agents import url_scrapper, url_analyzer, pdf_analyzer, financial_report_generator
from crewai import Task
from BizAgent.tools.tools import  web_scraping_tool,search_tool,fetch_pdf_content



# Scraping Tasks
url_scrape_task = Task(
    description="""Thoroughly scrape the company website {url} and search in browser with the  help of company name scrap the necessary information from those links to get necessary information, focusing on:
    1. Strong performing areas
    2. Areas where the company faced challenges   
    3. Strategic focus areas for the future
    4. Details on software solutions and recurring revenue
    5. Regional performance and key markets
    6. Specific segments like Enterprise and Long-Term Care (LTC)
    7. financial report for current year""",
    expected_output="""A detailed report containing:
    1. Overview of the company's strong performing areas
    2. Summary of the challenges faced by the company
    3. List of strategic focus areas for the future
    4. Insights into the company's software solutions and recurring revenue growth
    5. Analysis of regional performance and key markets
    6. Breakdown of performance in specific segments like Enterprise and Long-Term Care (LTC)
    7. financial report for current year""",
    tools=[web_scraping_tool,search_tool],
    agent=url_scrapper
)

# Analyzing Task
url_analyze_task = Task(
    description="""Analyze the scraped content from {url} to create a comprehensive technology-focused report.use company name to search news and financial report related to it and extract necessary information to generate :
    1. Identify the specific technologies and tools the company is currently using across different areas of their operations.
    2. Determine the company's technological strengths, highlighting areas where they seem to be performing well or innovating.
    3. Uncover any technological weaknesses or gaps in their current stack.
    4. Assess the company's technological maturity and identify their focus areas for future technology development or adoption.
    5. Propose potential IT services or technologies that could address the company's needs, enhance their capabilities, or help them overcome identified challenges.
    6. Summary of financial data like profit percentage etc for current year
    7. Latest news about the company """,

    expected_output="""A detailed technology-focused report including:
    1. Company overview with insights into their technological positioning and digital maturity.
    2. Comprehensive analysis of the company's current technology stack, including:
       - Specific technologies and tools used in different operational areas
       - How these technologies are being applied
       - Any unique or innovative uses of technology
    3. Technology-based SWOT analysis:
       - Technological strengths: Areas where the company excels in tech usage or innovation
       - Technological weaknesses: Gaps or outdated systems in their current stack
       - Opportunities: Potential areas for technological improvement or adoption
       - Threats: Potential risks or challenges related to their current technology usage
    4. Analysis of the company's strong performing areas in terms of technology over the past year.
    5. Identified areas of struggle or challenges related to technology implementation or usage.
    6. The company's apparent focus areas for future technological development or adoption.
    7. Specific recommendations for IT services or technologies that your company could provide, including:
       - How these services align with the client's technological needs and future focus
       - The potential impact of these services on the client's technological capabilities and business operations
       - A strategy for approaching the company with these technology-focused service offerings
    8. Any additional insights or observations about the company's overall technological strategy or digital transformation efforts.
    9. financial report for current year just a rough figure 
    10.latest News about the company just headlines not any links search in internet or collect information from the scrapped website data use the tool""",
    tools = [search_tool],
    agent=url_analyzer,
    depends_on=url_scrape_task,
    output_file="url_service_opportunity.md"
)



url_final_report_task = Task(
    description="Generate a final report by combining the outputs of the URL scraping and analysis tasks.",
    expected_output="A comprehensive final report that includes the results from both the URL scraping and analysis tasks.",
    agent=url_analyzer,
    depends_on=[url_scrape_task, url_analyze_task],
    output_file="final_report.md")




pdf_reading_task = Task(
        description="Get the content from the PDF {pdf_url} ",
        agent=pdf_analyzer,
        expected_output="content extracted from the pdf",
        tools = [fetch_pdf_content],
)


pdf_analyze_task = Task(
    description="""Analyze the extracted content  from pdf {pdf_url} to create a comprehensive technology-focused report.use company name to search news and financial report related to it and extract necessary information to generate :
    1. Identify the specific technologies and tools the company is currently using across different areas of their operations.
    2. Determine the company's technological strengths, highlighting areas where they seem to be performing well or innovating.
    3. Uncover any technological weaknesses or gaps in their current stack.
    4. Assess the company's technological maturity and identify their focus areas for future technology development or adoption.
    5. Propose potential IT services or technologies that could address the company's needs, enhance their capabilities, or help them overcome identified challenges.
    6. Summary of financial data like profit percentage etc for current year
    7. Latest news about the company """,
    
    expected_output="""A detailed technology-focused report including:
    1. Company overview with insights into their technological positioning and digital maturity.
    2. Comprehensive analysis of the company's current technology stack, including:
       - Specific technologies and tools used in different operational areas
       - How these technologies are being applied
       - Any unique or innovative uses of technology
    3. Technology-based SWOT analysis:
       - Technological strengths: Areas where the company excels in tech usage or innovation
       - Technological weaknesses: Gaps or outdated systems in their current stack
       - Opportunities: Potential areas for technological improvement or adoption
       - Threats: Potential risks or challenges related to their current technology usage
    4. Analysis of the company's strong performing areas in terms of technology over the past year.
    5. Identified areas of struggle or challenges related to technology implementation or usage.
    6. The company's apparent focus areas for future technological development or adoption.
    7. Specific recommendations for IT services or technologies that your company could provide, including:
       - How these services align with the client's technological needs and future focus
       - The potential impact of these services on the client's technological capabilities and business operations
       - A strategy for approaching the company with these technology-focused service offerings
    8. Any additional insights or observations about the company's overall technological strategy or digital transformation efforts.
    9. financial report for latest year  detailed report or information available  
    10.latest News about the company just headlines not any links""",
    
    agent=pdf_analyzer,
    tools = [search_tool],
    output_file="pdf_service_opportunity.md"
)

generate_financial_task = Task(
    description="""
        Use the tool provided to generate a comprehensive financial report 
        in markdown format using the provided company name.
    """,
    expected_output="Markdown report saved at media/financial_report.md",
    agent=financial_report_generator,
    async_execution=False,
    output_file="media/financial_report.md"
)