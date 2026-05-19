import requests
from supabase import create_client
import os, hashlib, time

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://bidplus.gem.gov.in/bidlists",
    "Origin": "https://bidplus.gem.gov.in",
}

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"  ✅ {tender['title'][:70]}")
    except Exception as e:
        print(f"  ❌ DB Error: {e}")

def fetch_gem_bids():
    """Fetch real live bids from GeM portal API"""
    print("🔍 Fetching GeM live bids...")
    total_saved = 0

    # GeM bidplus API - paginated
    for page in range(1, 6):  # 5 pages = ~500 bids
        try:
            url = f"https://bidplus.gem.gov.in/all-bids-data"
            params = {
                "page_no": page,
                "search_bids": "",
            }
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            
            if r.status_code != 200:
                print(f"  Page {page}: HTTP {r.status_code}")
                continue

            data = r.json()
            bids = data.get("data", [])
            
            if not bids:
                print(f"  Page {page}: No bids found")
                break

            print(f"  Page {page}: {len(bids)} bids")

            for bid in bids:
                bid_no = str(bid.get("bid_number", "") or bid.get("bidNo", ""))
                title = str(bid.get("item_name", "") or bid.get("itemName", "") or bid.get("title", ""))
                org = str(bid.get("ministry_name", "") or bid.get("ministryName", "") or bid.get("org_name", "") or "Government")
                state = str(bid.get("state", "") or "Central")
                value = bid.get("estimated_amount", 0) or bid.get("estimatedAmount", 0) or 0
                deadline = str(bid.get("end_date", "") or bid.get("endDate", "") or "")
                category = str(bid.get("product_category", "") or bid.get("category", "") or "government")
                source_url = f"https://bidplus.gem.gov.in/showbidDocument/{bid_no}" if bid_no else "https://gem.gov.in"

                if len(title) < 5:
                    continue

                save({
                    "tender_id": make_id("GEM" + bid_no + title[:20]),
                    "title": title[:500],
                    "organization": org[:200],
                    "state": state[:100],
                    "category": category[:100].lower(),
                    "value": int(float(str(value).replace(",", ""))) if value else None,
                    "source": "GeM",
                    "source_url": source_url,
                    "status": "active",
                    "deadline": deadline[:10] if deadline else None,
                })
                total_saved += 1

            time.sleep(2)  # Be polite to server

        except Exception as e:
            print(f"  Page {page} error: {e}")
            time.sleep(3)

    return total_saved

def fetch_gem_categories():
    """Fetch bids by category for more coverage"""
    print("🔍 Fetching GeM by categories...")
    total_saved = 0

    categories = [
        "Computer Hardware",
        "Office Furniture", 
        "Medical Equipment",
        "Construction",
        "Vehicle",
        "Solar Energy",
        "CCTV",
        "Network Equipment",
    ]

    for cat in categories:
        try:
            url = "https://bidplus.gem.gov.in/all-bids-data"
            params = {
                "page_no": 1,
                "search_bids": cat,
            }
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            
            if r.status_code != 200:
                continue

            data = r.json()
            bids = data.get("data", [])
            print(f"  {cat}: {len(bids)} bids")

            for bid in bids:
                bid_no = str(bid.get("bid_number", "") or "")
                title = str(bid.get("item_name", "") or bid.get("title", ""))
                org = str(bid.get("ministry_name", "") or bid.get("org_name", "") or "Government")
                state = str(bid.get("state", "") or "Central")
                value = bid.get("estimated_amount", 0) or 0
                deadline = str(bid.get("end_date", "") or "")

                if len(title) < 5:
                    continue

                save({
                    "tender_id": make_id("GEM-CAT" + bid_no + title[:20]),
                    "title": title[:500],
                    "organization": org[:200],
                    "state": state[:100],
                    "category": cat.lower().replace(" ", "_"),
                    "value": int(float(str(value).replace(",", ""))) if value else None,
                    "source": "GeM",
                    "source_url": f"https://bidplus.gem.gov.in/showbidDocument/{bid_no}",
                    "status": "active",
                    "deadline": deadline[:10] if deadline else None,
                })
                total_saved += 1

            time.sleep(1)

        except Exception as e:
            print(f"  {cat} error: {e}")

    return total_saved

if __name__ == "__main__":
    print("🚀 GeM Real Scraper Starting...")
    
    t1 = fetch_gem_bids()
    t2 = fetch_gem_categories()
    
    total = supabase.table("tenders").select("id", count="exact").execute()
    print(f"\n✅ Done! Saved {t1 + t2} new GeM tenders")
    print(f"📊 Total in DB: {total.count}")
