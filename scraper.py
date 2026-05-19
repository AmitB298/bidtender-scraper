import requests
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os, hashlib, time, json

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Referer": "https://eprocure.gov.in/",
}

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:70]}")
    except Exception as e:
        print(f"❌ {e}")

def scrape_epublish():
    """epublish.gov.in - CPPP published tenders, no CAPTCHA"""
    print("🔍 Scraping eProcure Published Tenders...")
    total = 0
    for page in range(0, 10):
        try:
            url = f"https://eprocure.gov.in/epublish/app?page=FrontEndLatestActiveTenders&service=page&currentPage={page}"
            r = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")
            
            rows = soup.select("table tr")
            count = 0
            for row in rows:
                cols = row.select("td")
                if len(cols) >= 5:
                    ref = cols[0].get_text(strip=True)
                    title = cols[2].get_text(strip=True)
                    org = cols[1].get_text(strip=True)
                    deadline = cols[4].get_text(strip=True)
                    
                    skip = ["search","active tender","version","contents","mis report","tender id","select sort"]
                    if any(w in title.lower() for w in skip):
                        continue
                    if len(title) > 15:
                        save({
                            "tender_id": make_id("EP-" + ref + title[:50]),
                            "title": title[:500],
                            "organization": org[:200],
                            "state": "Central",
                            "category": "government",
                            "source": "eProcure",
                            "source_url": "https://eprocure.gov.in",
                            "status": "active"
                        })
                        count += 1
            print(f"  Page {page+1}: {count} tenders")
            total += count
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Page {page}: {e}")
    print(f"  Total: {total}")

def scrape_gem_api():
    """GeM open search API"""
    print("🔍 Scraping GeM API...")
    try:
        url = "https://bidplus.gem.gov.in/getAllBidding"
        params = {"searchedBid": "", "page": 1}
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = r.json()
        bids = data.get("data", {}).get("bidList", []) or data.get("bidList", [])
        print(f"  Found {len(bids)} bids")
        for bid in bids:
            title = bid.get("bid_title") or bid.get("name") or ""
            org = bid.get("ministry") or bid.get("dept") or "GeM"
            bid_no = bid.get("bid_number") or bid.get("id") or ""
            if len(title) > 5:
                save({
                    "tender_id": make_id("GEM-" + str(bid_no) + title[:30]),
                    "title": title[:500],
                    "organization": org[:200],
                    "state": "Central",
                    "category": "government",
                    "source": "GeM",
                    "source_url": f"https://bidplus.gem.gov.in/bidlists",
                    "status": "active"
                })
    except Exception as e:
        print(f"  ❌ GeM: {e}")

def scrape_defence():
    """Defence procurement portal"""
    print("🔍 Scraping Defence Tenders...")
    try:
        url = "https://defproc.gov.in/nicgep/app?page=FrontEndLatestActiveTenders&service=page"
        r = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr")
        count = 0
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 3:
                title = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                org = cols[0].get_text(strip=True)
                if len(title) > 15 and "tender" not in title.lower()[:10]:
                    save({
                        "tender_id": make_id("DEF-" + title),
                        "title": title[:500],
                        "organization": org[:200],
                        "state": "Central",
                        "category": "defense",
                        "source": "Defence Procurement",
                        "source_url": url,
                        "status": "active"
                    })
                    count += 1
        print(f"  Defence: {count} tenders")
    except Exception as e:
        print(f"  ❌ Defence: {e}")

if __name__ == "__main__":
    print("🚀 BidTenderAssist Scraper v5")
    scrape_epublish()
    scrape_gem_api()
    scrape_defence()
    print("\n✅ All done!")