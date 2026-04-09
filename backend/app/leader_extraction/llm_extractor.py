import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.core.config import GROQ_API_KEY

load_dotenv()
client = Groq(api_key=GROQ_API_KEY)

# Load Kanini partner companies — path relative to backend root
KANINI_PARTNERS = []
try:
    _data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'companies.json')
    with open(_data_path, 'r') as f:
        data = json.load(f)
        KANINI_PARTNERS = [c['name'].lower() for c in data['companies']]
except:
    pass


def extract_leaders_from_text(company_name: str, scraped_text: str = "") -> list:
    """Ask LLM to extract up to 15 candidates with role scope validation."""

    is_partner = company_name.lower() in KANINI_PARTNERS
    priority_note = "\n\nNOTE: This is a Kanini partner company. Prioritize accuracy and provide comprehensive executive data." if is_partner else ""

    if scraped_text:
        prompt = f"""You are an expert at extracting C-suite executive information. Extract CURRENT executives from {company_name}.

SCRAPED TEXT:
{scraped_text}

TASK: Extract the TOP 5-10 CURRENT C-suite executives at {company_name} as of 2024-2025.

IF the scraped text has executive names, extract them.
IF the scraped text is incomplete or unclear, use your knowledge of {company_name}'s current leadership team.

EXTRACT (in order of importance):
1. CEO / President / Founder (if active)
2. CFO (Chief Financial Officer)
3. COO (Chief Operating Officer)
4. CTO / CIO (Chief Technology/Information Officer)
5. CMO (Chief Marketing Officer)
6. Other C-suite: Chief Product Officer, Chief People Officer, etc.
7. EVP / SVP (Executive/Senior Vice Presidents)

CRITICAL RULES:
- ONLY extract people who CURRENTLY work at {company_name} in 2024-2025
- DO NOT extract former executives, retired leaders, or historical founders
- DO NOT extract executives from OTHER companies mentioned in text
- If you're unsure, use your knowledge of {company_name}'s current leadership

Return JSON array (5-10 executives):
[{{"name":"First Last","title":"Current Title","role_scope":"parent","confidence":0.8}}]

IMPORTANT: {company_name} is a well-known company. You should be able to provide at least 3-5 current executives even if the scraped text is incomplete.{priority_note}"""
    else:
        prompt = f"""You are an expert at identifying C-suite executives. List the CURRENT top executives at {company_name} as of 2024-2025.

COMPANY: {company_name}

TASK: Provide the TOP 5-10 CURRENT C-suite executives based on your knowledge.

EXTRACT (in order of importance):
1. CEO / President / Founder (if currently active)
2. CFO (Chief Financial Officer)
3. COO (Chief Operating Officer)
4. CTO / CIO (Chief Technology/Information Officer)
5. CMO (Chief Marketing Officer)
6. Other C-suite officers
7. EVP / SVP (if prominent)

CRITICAL:
- ONLY list people who CURRENTLY hold these positions in 2024-2025
- DO NOT list former/retired executives
- Use your most recent knowledge of {company_name}'s leadership

Return JSON array (5-10 executives):
[{{"name":"First Last","title":"Current Title","role_scope":"parent","confidence":0.7}}]

IMPORTANT: {company_name} is a well-known company. Provide at least 3-5 current executives based on your knowledge. Only return [] if you truly know NOTHING about this company.{priority_note}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        print(f"LLM Response: {content[:300]}...")

        if '[' in content and ']' in content:
            start = content.index('[')
            end = content.rindex(']') + 1
            json_str = content[start:end]

            try:
                leaders = json.loads(json_str)

                valid_leaders = []
                for leader in leaders:
                    scope = leader.get("role_scope", "parent")
                    title = leader.get("title", "").lower()

                    non_exec_keywords = ['manager', 'director', 'lead', 'head of']
                    is_non_exec = any(keyword in title for keyword in non_exec_keywords)

                    exec_keywords = ['ceo', 'coo', 'cto', 'cio', 'cfo', 'cmo', 'chief', 'president', 'founder', 'evp', 'svp', 'chairman']
                    is_exec = any(keyword in title for keyword in exec_keywords)

                    if scope != "division" and is_exec and not is_non_exec:
                        valid_leaders.append(leader)
                    else:
                        print(f"  Filtered non-executive: {leader.get('name')} - {leader.get('title')}")

                return valid_leaders
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return []
    except Exception as e:
        print(f"LLM Error: {e}")

    return []
