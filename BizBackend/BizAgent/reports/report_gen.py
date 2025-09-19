import warnings
from crewai import Agent, Task
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

warnings.filterwarnings("ignore", category=UserWarning)
 # Assuming you have a utility function to read text files

# Load environment variables
load_dotenv()

# Load Google API key
google_api_key = os.getenv('GOOGLE_API_KEY')

google_api_key1 = os.getenv('GOOGLE_API_KEY1')

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    api_key=google_api_key,
    model="gemini-2.5-pro",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
)

llm2 = ChatGoogleGenerativeAI(
    api_key=google_api_key1,
    model="gemini-2.5-pro",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
)

class UrlReportGeneratorAgent(Agent):
    def __init__(self, *args, **kwargs):
        role = "Report Generator"
        goal = "Generate detailed comparison reports between companies"
        backstory = "An AI agent designed to analyze company documents and generate comprehensive reports."

        super().__init__(
            *args,
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            **kwargs
        )

    def text_reading_task(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()

    def report_generation_task(self, company_doc: str, target_company_doc: str, prompt_template: str):
        llm_input = prompt_template.format(target_company_doc, company_doc)
        return self.llm.invoke(llm_input)

    def save_report_to_file(self, report_content: str, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(report_content)
        print(f"Report saved to {file_path}")

    def run(self, company_doc_path: str, target_company_doc_path: str, prompt_template: str):
        company_doc = self.text_reading_task(company_doc_path)
        target_company_doc = self.text_reading_task(target_company_doc_path)

        report = self.report_generation_task(company_doc, target_company_doc, prompt_template)

        report_text = report.content if hasattr(report, "content") else str(report)
        output_file_path = "media/comparison_report.md"

        self.save_report_to_file(report_text, output_file_path)
        return output_file_path
    

class PdfReportGeneratorAgent(Agent):
    def __init__(self, *args, **kwargs):
        role = "Report Generator"
        goal = "Generate detailed comparison reports between companies"
        backstory = "An AI agent designed to analyze company documents and generate comprehensive reports."

        super().__init__(
            *args,
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm2,
            **kwargs
        )

    def text_reading_task(self, file_path: str):
        """Fetch the content from the text file with utf-8 encoding."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Fallback to 'latin-1' if utf-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
        return content

    def report_generation_task(self, company_doc: str, target_company_doc: str, prompt_template: str):
        """Generate a comparison report using the Gemini LLM."""
        llm_input = prompt_template.format(
            target_company_doc,  # This corresponds to {0}
            company_doc          # This corresponds to {1}
        )
        report = llm2.invoke(llm_input)
        return report   
    def save_report_to_file(self, report_content: str, file_path: str):
        """Save the report content to a .txt file."""
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(report_content)
        print(f"Report saved to {file_path}")

    def run(self, company_doc_path: str, target_company_doc_path: str, prompt_template: str):
        """Run the agent to generate the report and save it to a file."""
        # Fetch company documents (both text files)
        company_doc = self.text_reading_task(company_doc_path)
        target_company_doc = self.text_reading_task(target_company_doc_path)

        # Generate the report
        report_task = self.report_generation_task(company_doc, target_company_doc, prompt_template)

        # Save the report to a .txt file
        output_file_path = "comparison_report.md"
        self.save_report_to_file(report_task.content, output_file_path)

        # Return the path to the saved report file
        return output_file_path