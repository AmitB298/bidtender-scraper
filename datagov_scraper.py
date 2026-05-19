import requests
from supabase import create_client
from dotenv import load_dotenv
import os
import hashlib

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# data.gov.in free API - no key needed for public datasets
DATASETS = [
    "https://api.data.gov.in/resource/e4c3c8f7-0c51-4d2b-9c82-d09efab61f2c?api-key=579b464db66ec23bdd000001cdd3946e44ce4aad38534d4292f5c90&format=json&limit=100",
]

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save_tender(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def fetch_datagov():
    print("🔍 Fetching from data.gov.in...")
    url = "https://api.data.gov.in/resource/e4c3c8f7-0c51-4d2b-9c82-d09efab61f2c"
    params = {
        "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad38534d4292f5c90",
        "format": "json",
        "limit": 100
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        records = data.get("records", [])
        print(f"  Found {len(records)} records")
        for rec in records:
            title = rec.get("tender_title") or rec.get("title") or rec.get("name") or ""
            if len(title) < 5:
                continue
            save_tender({
                "tender_id": make_id(str(rec)),
                "title": title[:500],
                "organization": rec.get("organization") or rec.get("dept") or "Government",
                "state": rec.get("state") or "Central",
                "category": "government",
                "value": int(rec.get("value") or rec.get("amount") or 0) or None,
                "source": "data.gov.in",
                "source_url": "https://data.gov.in",
                "status": "active"
            })
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 data.gov.in Scraper Starting...")
    fetch_datagov()
    print("✅ Done!")