import os
import sys
import asyncio
sys.path.append("BizBackend")
import yfinance as yf
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from docx import Document 
from BizAgent.reports.md_to_Docx import convert_md_to_docx


api_key="AIzaSyDtFzc2Be-2Xhx0WQQgSi2nMQpqhc05v-E"
# api_key = os.getenv('GOOGLE_API_KEY')

def extract_company_name_from_md(file_path): 
    """Extracts the company's correct name from a markdown report using Gemini LLM."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()
            print(md_content)

        llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-2.0-flash", temperature=0.2)
        prompt_template = ChatPromptTemplate.from_messages([
            ("human", """
            I have the following markdown report content:

            {md_content}

            From this content, identify the company's correct name. Please extract only the name of the company.
            """),
        ])

        llm_chain = LLMChain(llm=llm, prompt=prompt_template)
        response = llm_chain.run(md_content=md_content)
        return response.strip()
    except Exception as e:
        print(f"Error extracting company name: {e}")
        return None

def get_ticker_symbol_with_llm(company_name,api_key):
    """Fetches the ticker symbol for a given company name using Gemini LLM."""
    try:
        llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-2.0-flash", temperature=0.2)
        prompt_template = ChatPromptTemplate.from_messages([
            ("human", """
            I need the stock ticker symbol for the following company:

            Company Name: {company_name}

            Please provide the ticker symbol.
            Do not include any additional letters or symbols, just the ticker symbol.
            For example, if the company is "Apple Inc.", the ticker symbol is "AAPL"
            """),
        ])

        llm_chain = LLMChain(llm=llm, prompt=prompt_template)
        response = llm_chain.run(company_name=company_name)
        return response.strip()

    except Exception as e:
        print(f"Error fetching ticker symbol: {e}")
        return None

def fetch_financial_data(ticker_symbol):
    """Fetches financial data (Balance Sheet, Income Statement, Cash Flow) for a company using yfinance."""
    try:
        stock_data = yf.Ticker(ticker_symbol)
        balance_sheet = stock_data.balance_sheet
        income_statement = stock_data.financials
        cashflow_statement = stock_data.cashflow

        def prepare_financial_data(dataframe, title):
            if dataframe is None or dataframe.empty:
                return f"No {title} data available."
            return dataframe.to_dict()

        return {
            "Balance Sheet": prepare_financial_data(balance_sheet, "Balance Sheet"),
            "Income Statement": prepare_financial_data(income_statement, "Income Statement"),
            "Cash Flow Statement": prepare_financial_data(cashflow_statement, "Cash Flow Statement"),
        }

    except Exception as e:
        print(f"Error fetching financial data: {e}")
        return None

def generate_financial_report(financial_data,api_key ,company_name):
    """Generates a financial report using Gemini with LangChain and an API key."""
    try:
        llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-2.0-flash", temperature=0.2)
        chat_template = ChatPromptTemplate.from_messages([
            ("human", """
            Here is the financial data for {company_name}:

            Balance Sheet:
            {balance_sheet}

            Income Statement:
            {income_statement}

            Cash Flow Statement:
            {cashflow_statement}

            Answer the following questions based on the data:
            1. Provide a summary of the financial data, including profit percentages and key performance indicators for the current year.
            2. Generate a financial report for the latest year with detailed insights.
            3. How was the financial performance throughout the year?
            4. What was the overall topline and bottomline revenue for the current year?
            5. What was the overall profit margin for the current year?
            6. Provide quarterly revenue and profit margins for the current year.
            7. Which services or solutions brought the highest revenue and profits?
            8. Which regions performed well in terms of overall revenues?
            9. Specify the investments made during the current year.
            10. Highlight the departments or divisions that underperformed.
            11. How does the company perform in terms of sustainability and ESG goals?
            12. List top initiatives for attracting and retaining talent.
            13. Did the company retrench any employees during the year?
            14. Explain each department or function mentioned in the report, providing insights about performance.
            15. Describe management discussions, key takeaways, and the financial condition of the company, along with operational results.
            16. Compare the company's performance in 2024 with 2023.
            17. Are there any ongoing legal battles involving the company?
            18. Summarize market sentiment regarding the company.
             
             Note :
             1. Use companys name in the report wherever required {company_name}
             2. Try giving answer for all questions or else retry the question and find the answer.
             3. If answer cannot be found give that answer cannot be found.
             4. Do not hallucinate and give answers.Give answer from the financial data
            """)
        ])

        llm_chain = LLMChain(llm=llm, prompt=chat_template)
        response = llm_chain.run(
            balance_sheet=financial_data["Balance Sheet"],
            income_statement=financial_data["Income Statement"],
            cashflow_statement=financial_data["Cash Flow Statement"],
            company_name=company_name
        )
        return response
        

    except Exception as e:
        print(f"Error generating report: {e}")
        return None

def save_report_to_md(report, output_path):
    """Saves the financial report as a markdown file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(report)
        print(f"Report saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving report: {e}")
        return False

def append_markdown_files(merged_url_path, financial_report_path, output_path):
    """
    Appends the financial report content to the merged URL report with a heading.
    """
    try:
        # Read merged URL content
        with open(merged_url_path, "r", encoding="utf-8") as merged_file:
            merged_content = merged_file.read()

        # Read financial report content
        with open(financial_report_path, "r", encoding="utf-8") as financial_file:
            financial_content = financial_file.read()

        # Add heading before the financial report content
        heading = "\n\n## Financial Report from External Sources\n\n"
        final_content = merged_content + heading + financial_content

        # Save the result to the output file
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(final_content)

        print(f"Appended content with heading saved to {output_path}")
        return True

    except Exception as e:
        print(f"Error appending markdown with heading: {e}")
        return False

def run_financial_report_pipeline(company_name: str) -> str:
    try:
        output_md_path = "media/financial_report.md"
        ticker_symbol = get_ticker_symbol_with_llm(company_name, api_key)

        if not ticker_symbol:
            raise ValueError("Ticker symbol not found")

        financial_data = fetch_financial_data(ticker_symbol)
        if not financial_data:
            raise ValueError("Financial data not found")

        financial_report = generate_financial_report(financial_data, api_key, company_name)
        if not financial_report:
            raise ValueError("Financial report could not be generated")

        save_report_to_md(financial_report, output_md_path)
        return output_md_path
    except Exception as e:
        print(f"Error in financial pipeline: {e}")
        return None
