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
        print(f"✅ {tender['title'][:70]}")
    except Exception as e:
        print(f"❌ {e}")

def scrape_cppp():
    print("🔍 Scraping CPPP...")
    total = 0
    for page in range(1, 11):
        try:
            url = f"https://eprocure.gov.in/eprocure/app?page=FrontEndLatestActiveTenders&service=page&currentPage={page}"
            r = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # CPPP table has id="table"
            table = soup.find("table", {"id": "table"})
            if not table:
                table = soup.find("table", class_=lambda x: x and "list" in x.lower())
            if not table:
                tables = soup.find_all("table")
                table = tables[1] if len(tables) > 1 else None
            
            if not table:
                print(f"  Page {page}: No table found")
                break
                
            rows = table.find_all("tr")[1:]  # skip header
            count = 0
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    tender_id_text = cols[0].get_text(strip=True)
                    title = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    org = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    deadline = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                    
                    # Skip if title looks like navigation
                    skip_words = ["search", "active tender", "corrigendum", "version", "contents owned", "mis report"]
                    if any(w in title.lower() for w in skip_words):
                        continue
                    
                    if len(title) > 10:
                        save({
                            "tender_id": make_id("CPPP-" + tender_id_text + title[:50]),
                            "title": title[:500],
                            "organization": org[:200],
                            "state": "Central",
                            "category": "government",
                            "source": "CPPP",
                            "source_url": "https://eprocure.gov.in",
                            "status": "active"
                        })
                        count += 1
            
            print(f"  Page {page}: {count} real tenders")
            total += count
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Page {page}: {e}")
            break
    print(f"  Total CPPP: {total} tenders")

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
            if len(title) > 20 and any(w in title.lower() for w in ["tender","supply","work","contract","bid","rfp","notice","procurement"]):
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

if __name__ == "__main__":
    print("🚀 BidTenderAssist Scraper v4")
    scrape_cppp()
    scrape_coalindia()
    print("\n✅ All done!")