import requests
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os, hashlib, time

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def scrape(url, org, state, category):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        count = 0
        for a in links:
            title = a.get_text(strip=True)
            href = a["href"]
            if len(title) > 30 and any(w in title.lower() for w in ["tender","bid","rfp","supply","work","contract","procurement"]):
                full_url = href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")
                save({
                    "tender_id": make_id(org + title),
                    "title": title[:500],
                    "organization": org,
                    "state": state,
                    "category": category,
                    "source": org,
                    "source_url": full_url,
                    "status": "active"
                })
                count += 1
        print(f"  {org}: {count} tenders saved")
        time.sleep(2)
    except Exception as e:
        print(f"  ❌ {org}: {e}")

SOURCES = [
    ("https://ntpctender.com/tenders/", "NTPC", "Central", "infrastructure"),
    ("https://www.nhai.gov.in/tender-list", "NHAI", "Central", "construction"),
    ("https://www.bhel.com/tenders", "BHEL", "Central", "infrastructure"),
    ("https://www.iocl.com/tenders", "IOCL", "Central", "infrastructure"),
    ("https://www.coalindia.in/en-us/business/tenders.aspx", "Coal India", "Central", "infrastructure"),
    ("https://www.ongcindia.com/wps/wcm/connect/en/home/tender", "ONGC", "Central", "infrastructure"),
    ("https://mahatenders.gov.in", "Maharashtra PWD", "Maharashtra", "construction"),
    ("https://etender.up.nic.in", "UP Government", "Uttar Pradesh", "government"),
    ("https://eproc.rajasthan.gov.in", "Rajasthan Government", "Rajasthan", "government"),
    ("https://mpeproc.gov.in", "MP Government", "Madhya Pradesh", "government"),
]

if __name__ == "__main__":
    print("🚀 PSU + State Tender Scraper Starting...")
    for url, org, state, cat in SOURCES:
        print(f"\n🔍 Scraping {org}...")
        scrape(url, org, state, cat)
    print("\n✅ All done!")