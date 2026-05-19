import requests
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os, hashlib, time

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def scrape_cppp():
    print("🔍 Scraping CPPP...")
    for page in range(1, 6):
        try:
            url = f"https://eprocure.gov.in/eprocure/app?page=FrontEndLatestActiveTenders&service=page&currentPage={page}"
            r = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.select("table tr")[1:]
            count = 0
            for row in rows:
                cols = row.select("td")
                if len(cols) >= 4:
                    title = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    org = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    deadline = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                    ref = cols[0].get_text(strip=True) if cols else ""
                    if len(title) > 10:
                        save({
                            "tender_id": make_id("CPPP-" + ref + title),
                            "title": title[:500],
                            "organization": org[:200],
                            "state": "Central",
                            "category": "government",
                            "source": "CPPP",
                            "source_url": "https://eprocure.gov.in",
                            "status": "active"
                        })
                        count += 1
            print(f"  Page {page}: {count} tenders")
            time.sleep(3)
        except Exception as e:
            print(f"  ❌ Page {page}: {e}")

def scrape_gem():
    print("🔍 Scraping GeM...")
    try:
        url = "https://bidplus.gem.gov.in/all-bids"
        r = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        # GeM bid cards
        cards = soup.select(".bid-details-card, .card-body, div[class*='bid']")
        count = 0
        for card in cards:
            title = card.get_text(strip=True)
            if len(title) > 20:
                save({
                    "tender_id": make_id("GEM-" + title[:100]),
                    "title": title[:500],
                    "organization": "GeM Portal",
                    "state": "Central",
                    "category": "government",
                    "source": "GeM",
                    "source_url": url,
                    "status": "active"
                })
                count += 1
        print(f"  GeM: {count} tenders")
    except Exception as e:
        print(f"  ❌ GeM: {e}")

def scrape_coalindia():
    print("🔍 Scraping Coal India...")
    try:
        url = "https://www.coalindia.in/en-us/business/tenders.aspx"
        r = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        count = 0
        for a in links:
            title = a.get_text(strip=True)
            href = a["href"]
            if len(title) > 20 and any(w in title.lower() for w in ["tender","supply","work","contract","bid","rfp","notice"]):
                save({
                    "tender_id": make_id("COAL-" + title),
                    "title": title[:500],
                    "organization": "Coal India",
                    "state": "Central",
                    "category": "infrastructure",
                    "source": "Coal India",
                    "source_url": "https://www.coalindia.in" + href if href.startswith("/") else href,
                    "status": "active"
                })
                count += 1
        print(f"  Coal India: {count} tenders")
    except Exception as e:
        print(f"  ❌ Coal India: {e}")

def scrape_irctc():
    print("🔍 Scraping Indian Railways...")
    try:
        url = "https://www.indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,1,304,366,533"
        r = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        count = 0
        for a in links:
            title = a.get_text(strip=True)
            if len(title) > 20 and any(w in title.lower() for w in ["tender","bid","rfp","supply","work","contract"]):
                save({
                    "tender_id": make_id("IR-" + title),
                    "title": title[:500],
                    "organization": "Indian Railways",
                    "state": "Central",
                    "category": "infrastructure",
                    "source": "Indian Railways",
                    "source_url": url,
                    "status": "active"
                })
                count += 1
        print(f"  Railways: {count} tenders")
    except Exception as e:
        print(f"  ❌ Railways: {e}")

if __name__ == "__main__":
    print("🚀 BidTenderAssist Scraper v3")
    scrape_cppp()
    scrape_gem()
    scrape_coalindia()
    scrape_irctc()
    print("\n✅ All done!")