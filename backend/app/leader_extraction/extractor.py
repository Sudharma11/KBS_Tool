from app.leader_extraction.scraper import scrape_company_pages
from app.leader_extraction.llm_extractor import extract_leaders_from_text
from app.leader_extraction.verifier import verify_leader


def extract_leaders(company_name: str) -> list:
    """Extract up to 5 verified leaders and return in Name/Role/LinkedinURL/ImageURL format."""

    print(f"\n[1/3] Scraping {company_name} website...")
    scraped_text = scrape_company_pages(company_name)
    print(f"Scraped {len(scraped_text)} chars" if scraped_text else "No text scraped")

    print(f"\n[2/3] Extracting candidates with LLM...")
    candidates = extract_leaders_from_text(company_name, scraped_text)
    print(f"Found {len(candidates)} candidates")

    if not candidates and len(scraped_text) < 1000:
        print(f"  Low data quality, trying LLM knowledge...")
        candidates = extract_leaders_from_text(company_name, "")
        print(f"Found {len(candidates)} candidates from LLM knowledge")

    if not candidates:
        print(f"WARNING: No data available for {company_name}.")
        return []

    print(f"\n[3/3] Verifying candidates (need 5)...")
    verified_leaders = []
    seen_names = set()

    for candidate in candidates:
        if len(verified_leaders) >= 5:
            break

        name = candidate.get("name", "")
        title = candidate.get("title", "")
        role_scope = candidate.get("role_scope", "parent")
        confidence = candidate.get("confidence", 0.5)

        if not name or len(name.split()) < 2 or name.lower() in seen_names:
            continue

        verification = verify_leader(name, title, company_name, scraped_text)

        if verification["verified"]:
            confidence += verification["confidence_boost"]
            confidence = min(max(confidence, 0.0), 1.0)

            seen_names.add(name.lower())
            verified_leaders.append({
                "Name": name,
                "Role": title,
                "LinkedinURL": None,
                "ImageURL": None,
                "confidence": round(confidence, 2),
                "source": verification.get("source", ""),
                "verified": True,
                "method": verification.get("method", "unknown")
            })
            print(f"  [OK] {name} - {title} [{role_scope}] ({confidence:.2f}) - Progress: {len(verified_leaders)}/5")
        else:
            print(f"  [FAIL] {name} - Not verified")

    print(f"\n[3/3] Final: {len(verified_leaders)} verified leaders")

    print(f"\n[4/4] Enriching LinkedIn URLs...")
    from app.services.leader_search import enrich_linkedin
    verified_leaders = enrich_linkedin(verified_leaders, company_name)
    print(f"LinkedIn enrichment done.")

    return verified_leaders
