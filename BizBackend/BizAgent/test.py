import os
kanini_txt_path = r"BizInsightAnalyzer\BizBackend\BizAgent\Data\KANINI_SERVICES.txt"
if not os.path.exists(kanini_txt_path):
    print(f"Kanini summary file not found at {kanini_txt_path}")
else:
    print(f"Kanini summary file found at {kanini_txt_path}")

cwd = os.getcwd()
print(f"Current working directory: {cwd}")