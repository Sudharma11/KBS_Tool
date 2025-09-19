from spire.doc import *
from spire.doc.common import *

def convert_md_to_docx(md_file, docx_output):
    """
    Convert a Markdown file to DOCX format.
    
    Args:
        md_file (str): The path to the Markdown file.
        docx_output (str): The path for the DOCX output file.
    """
    # Create an object of the Document class
    document = Document()
    # Load a Markdown file
    document.LoadFromFile(md_file)

    # Save the Markdown file to a Word DOCX file
    document.SaveToFile(docx_output, FileFormat.Docx)
    # Save the Markdown file to a Word DOC file
    # document.SaveToFile("MdToDoc.doc", FileFormat.Doc)
    document.Close()
    
    print(f"Conversion complete: '{md_file}' converted to '{docx_output}'.")



