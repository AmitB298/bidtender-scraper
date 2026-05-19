import requests
import xml.etree.ElementTree as ET
from supabase import create_client
from dotenv import load_dotenv
import os
import hashlib
from datetime import datetime

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

RSS_FEEDS = [
    "https://eprocure.gov.in/eprocure/app?page=FrontEndTendersByOrganisation&service=rss",
    "https://gem.gov.in/rss/tenders",
]

def save_tender(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def scrape_rss(url, source_name):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        print(f"📡 {source_name}: {len(items)} items found")
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            if not title:
                continue
            tender_id = hashlib.md5(f"{source_name}-{link or title}".encode()).hexdigest()
            tender = {
                "tender_id": tender_id[:50],
                "title": title[:500],
                "description": desc[:1000],
                "source": source_name,
                "source_url": link or url,
                "state": "Central",
                "category": "government",
                "status": "active",
            }
            save_tender(tender)
    except Exception as e:
        print(f"❌ {source_name} Error: {e}")

if __name__ == "__main__":
    print("🚀 RSS Scraper Starting...")
    for feed in RSS_FEEDS:
        scrape_rss(feed, "CPPP" if "eprocure" in feed else "GeM")
    print("✅ Done!")