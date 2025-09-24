import warnings
from crewai import Agent
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
load_dotenv()

# --- Language Model Configurations ---
llm_config = {
    "model": "gemini-2.5-pro", # Standardized model name
    "temperature": 0.2,
    "max_tokens": None,
    "timeout": None,
}

llm = ChatGoogleGenerativeAI(
    **llm_config,
    api_key=os.getenv('GOOGLE_API_KEY')
)

llm2 = ChatGoogleGenerativeAI(
    **llm_config,
    api_key=os.getenv('GOOGLE_API_KEY1')
)

# --- Report Generation Agent Classes ---

class UrlReportGeneratorAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            role="Comparison Report Specialist",
            goal="Generate a detailed comparison report between two companies based on provided documents.",
            backstory="An AI agent specializing in synthesizing information from multiple sources to create comprehensive, side-by-side business reports.",
            llm=llm,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )

    def _read_text_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return f"Error: Could not read content from {file_path}."

    def run(self, company_doc_path: str, target_company_doc_path: str, prompt_template: str):
        company_doc = self._read_text_file(company_doc_path)
        target_company_doc = self._read_text_file(target_company_doc_path)

        llm_input = prompt_template.format(target_company_doc, company_doc)
        response = self.llm.invoke(llm_input)
        
        report_text = response.content if hasattr(response, "content") else str(response)
        
        # This returns the content directly, letting the view handle file saving.
        return report_text

class PdfReportGeneratorAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            role="PDF Content Comparison Analyst",
            goal="Generate a detailed comparison report between two companies using content extracted from PDFs and other documents.",
            backstory="An AI agent designed to analyze and compare structured and unstructured data from various documents to produce insightful reports.",
            llm=llm2,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )

    def _read_text_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return f"Error: Could not read content from {file_path}."

    def run(self, company_doc_path: str, target_company_doc_path: str, prompt_template: str):
        company_doc = self._read_text_file(company_doc_path)
        target_company_doc = self._read_text_file(target_company_doc_path)
        
        llm_input = prompt_template.format(target_company_doc, company_doc)
        response = self.llm.invoke(llm_input)
        
        report_text = response.content if hasattr(response, "content") else str(response)
        
        return report_text

