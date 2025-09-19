import os
def merge_reports_to_final(comparison_md_path, financial_md_path, final_md_path):
    """Merge all three reports into a final report."""
    try:
        final_content = ""
# Read and add comparison report
        if os.path.exists(comparison_md_path):
            with open(comparison_md_path, "r", encoding="utf-8") as f:
                comparison_content = f.read()
            final_content += "# Competitive Analysis Report\n\n" + comparison_content + "\n\n"
        
        # Read and add financial report
        if os.path.exists(financial_md_path):
            with open(financial_md_path, "r", encoding="utf-8") as f:
                financial_content = f.read()
            final_content += "# Financial Analysis Report\n\n" + financial_content + "\n\n"
        # Save merged content
        with open(final_md_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        print(f"Final merged report saved to: {final_md_path}")
        return True
    except Exception as e:
        print(f"Error merging reports: {e}")
        return False