import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

def extract_company_name_from_md(file_path, api_key):
    """Extracts the company's correct name from a markdown report using Gemini LLM.

    Args:
        file_path: Path to the markdown file containing the company's report.
        api_key: Your Google API key for Gemini LLM.

    Returns:
        The company's correct name as a string, or None if extraction fails.
    """
    try:
        # Read the markdown file content
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()

        # Initialize the Gemini LLM client
        llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-2.0-flash",
            temperature=0.2,
        )

        # Define the prompt template for extracting the company's name
        prompt_template = ChatPromptTemplate.from_messages([
            ("human", """
            I have the following markdown report content:
            
            {md_content}
            
            From this content, identify the company's correct name. Please extract only the name of the company.
            """)
        ])

        # Create a LangChain instance with the LLM and prompt
        llm_chain = LLMChain(llm=llm, prompt=prompt_template)

        # Run the query to get the company's name
        response = llm_chain.run(md_content=md_content)

        return response.strip()

    except Exception as e:
        # Handle errors during LLM interaction
        print(f"Error extracting company name: {e}")
        return None

# Example Usage
if __name__ == "__main__":
    # Path to the markdown file
    md_file_path = r"D:\Business_Insights_Analyser 2\Business_Insights_Analyser\merged_url_report.md"
    
    # Replace with your actual API key
    google_api_key =  "AIzaSyCZHY8iwQAxSlmealI-HBBnHJyGSYgp4n4"

    print("Extracting company name from markdown file...")
    company_name = extract_company_name_from_md(md_file_path, google_api_key)

    if company_name:
        print(f"Extracted Company Name: {company_name}")
    else:
        print("Failed to extract the company's name.")
