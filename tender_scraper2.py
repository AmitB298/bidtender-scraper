import requests
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os
import hashlib
import time

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.5",
}

def save_tender(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def scrape_tendertiger():
    """TenderTiger - publicly visible tenders"""
    print("\n🔍 Scraping TenderTiger...")
    urls = [
        "https://www.tendertiger.com/tenders/construction-tenders.html",
        "https://www.tendertiger.com/tenders/it-tenders.html",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.select("table.tender-list tr, div.tender-item, tr.tender-row")
            print(f"  Found {len(rows)} rows at {url}")
            for row in rows[:20]:
                title = row.select_one("td:nth-child(2), .tender-title, a")
                org = row.select_one("td:nth-child(3), .org-name")
                if title and len(title.text.strip()) > 10:
                    t = {
                        "tender_id": make_id(title.text.strip()),
                        "title": title.text.strip()[:500],
                        "organization": org.text.strip()[:200] if org else "Unknown",
                        "state": "Central",
                        "category": "construction" if "construction" in url else "it",
                        "source": "TenderTiger",
                        "source_url": url,
                        "status": "active"
                    }
                    save_tender(t)
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ {e}")

def scrape_meraindia():
    """Mera India Tenders - public portal"""
    print("\n🔍 Scraping Mera India Tenders...")
    url = "https://www.meraindiatender.com/public-tenders.php"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr")
        print(f"  Found {len(rows)} rows")
        for row in rows[1:30]:
            cols = row.select("td")
            if len(cols) >= 3:
                title = cols[0].text.strip() if cols[0] else ""
                org = cols[1].text.strip() if len(cols) > 1 else ""
                state = cols[2].text.strip() if len(cols) > 2 else "Central"
                if len(title) > 10:
                    t = {
                        "tender_id": make_id(title + org),
                        "title": title[:500],
                        "organization": org[:200],
                        "state": state[:100],
                        "category": "government",
                        "source": "MeraIndiaTender",
                        "source_url": url,
                        "status": "active"
                    }
                    save_tender(t)
        time.sleep(2)
    except Exception as e:
        print(f"  ❌ {e}")

def scrape_eprocure():
    """eProcure CPPP - Active tenders page"""
    print("\n🔍 Scraping eProcure...")
    url = "https://eprocure.gov.in/eprocure/app?page=FrontEndLatestActiveTenders&service=page"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("#table tr")[1:]
        print(f"  Found {len(rows)} tenders")
        for row in rows[:30]:
            cols = row.select("td")
            if len(cols) >= 5:
                title = cols[2].text.strip()
                org = cols[1].text.strip()
                deadline = cols[4].text.strip()
                if len(title) > 5:
                    t = {
                        "tender_id": make_id(title + org),
                        "title": title[:500],
                        "organization": org[:200],
                        "state": "Central",
                        "category": "government",
                        "source": "CPPP",
                        "source_url": "https://eprocure.gov.in",
                        "status": "active"
                    }
                    save_tender(t)
        time.sleep(2)
    except Exception as e:
        print(f"  ❌ {e}")

if __name__ == "__main__":
    print("🚀 Real Tender Scraper v2 Starting...")
    scrape_eprocure()
    scrape_tendertiger()
    scrape_meraindia()
    print("\n✅ All done!")