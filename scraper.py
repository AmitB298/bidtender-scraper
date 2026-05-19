import requests
from supabase import create_client
from dotenv import load_dotenv
import os, hashlib, time

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# data.gov.in free API key (public)
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad38534d4292f5c90"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:70]}")
    except Exception as e:
        print(f"❌ {e}")

def fetch_datagov(resource_id, source_name, state="Central", category="government"):
    """Fetch from data.gov.in API"""
    print(f"🔍 Fetching {source_name}...")
    try:
        url = f"https://api.data.gov.in/resource/{resource_id}"
        params = {"api-key": API_KEY, "format": "json", "limit": 100, "offset": 0}
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = r.json()
        records = data.get("records", [])
        print(f"  Found {len(records)} records")
        for rec in records:
            # Try all possible title fields
            title = (rec.get("tender_title") or rec.get("title") or 
                    rec.get("work_name") or rec.get("name") or 
                    rec.get("description") or "")
            org = (rec.get("organization") or rec.get("dept_name") or 
                  rec.get("department") or rec.get("ministry") or "Government")
            tid = (rec.get("tender_id") or rec.get("ref_no") or 
                  rec.get("id") or make_id(str(rec)))
            value = rec.get("estimated_cost") or rec.get("value") or rec.get("amount") or 0
            
            if len(str(title)) > 10:
                save({
                    "tender_id": make_id(source_name + str(tid) + str(title)[:30]),
                    "title": str(title)[:500],
                    "organization": str(org)[:200],
                    "state": state,
                    "category": category,
                    "value": int(float(str(value).replace(",",""))) if value else None,
                    "source": source_name,
                    "source_url": "https://data.gov.in",
                    "status": "active"
                })
        time.sleep(1)
    except Exception as e:
        print(f"  ❌ {source_name}: {e}")

# Known tender datasets on data.gov.in
DATASETS = [
    # Format: (resource_id, name, state, category)
    ("9ef84268-d588-465a-a308-a864a43d0070", "GeM Tenders", "Central", "government"),
    ("6176ee09-3d56-4a3b-8115-21841576b2f6", "CPPP Tenders", "Central", "government"),
    ("c1e7b131-a8ab-4059-b3a2-f4e37e4ef6ab", "UP Tenders", "Uttar Pradesh", "government"),
    ("2c93e4a0-5c89-4461-a1c4-b82c7e31e9d2", "Maharashtra Tenders", "Maharashtra", "government"),
]

if __name__ == "__main__":
    print("🚀 BidTenderAssist Scraper v6 - data.gov.in")
    for resource_id, name, state, cat in DATASETS:
        fetch_datagov(resource_id, name, state, cat)
    print("\n✅ All done!")