import requests
from supabase import create_client
import os, hashlib, time
from xml.etree import ElementTree as ET

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json,text/html,*/*",
}

API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad38534d4292f5c90"

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"  ✅ {tender['title'][:70]}")
        return True
    except Exception as e:
        print(f"  ❌ {e}")
        return False

# ─── SOURCE 1: data.gov.in paginated — 500 records per dataset ───────────────
def fetch_datagov_paginated():
    print("\n📌 data.gov.in paginated fetch...")

    datasets = [
        ("9ef84268-d588-465a-a308-a864a43d0070", "GeM-Bids",     "Central",       "government"),
        ("6176ee09-3d56-4a3b-8115-21841576b2f6", "CPPP",         "Central",       "government"),
        ("c1e7b131-a8ab-4059-b3a2-f4e37e4ef6ab", "UP-Tenders",   "Uttar Pradesh", "government"),
        ("2c93e4a0-5c89-4461-a1c4-b82c7e31e9d2", "MH-Tenders",   "Maharashtra",   "government"),
        ("11b58964-7b49-4563-b4fe-a73e4dab3f40", "Defence",      "Central",       "defence"),
    ]

    saved = 0
    for resource_id, name, state, category in datasets:
        for offset in [0, 100, 200, 300, 400]:
            try:
                r = requests.get(
                    f"https://api.data.gov.in/resource/{resource_id}",
                    params={"api-key": API_KEY, "format": "json", "limit": 100, "offset": offset},
                    headers=HEADERS, timeout=20
                )
                if r.status_code != 200:
                    break

                records = r.json().get("records", [])
                if not records:
                    break

                print(f"  {name} offset={offset}: {len(records)} records")

                for rec in records:
                    title = (
                        rec.get("tender_title") or rec.get("title") or
                        rec.get("work_name") or rec.get("item_description") or
                        rec.get("name") or ""
                    )
                    if len(str(title)) < 10:
                        continue

                    org = (
                        rec.get("organisation_name") or rec.get("organization") or
                        rec.get("dept_name") or rec.get("ministry") or "Government"
                    )
                    value = (
                        rec.get("estimated_amount") or rec.get("estimated_cost") or
                        rec.get("value") or rec.get("amount") or 0
                    )
                    tid = rec.get("tender_id") or rec.get("bid_number") or rec.get("ref_no") or make_id(str(rec))
                    deadline = rec.get("closing_date") or rec.get("end_date") or ""

                    ok = save({
                        "tender_id": make_id(name + str(tid) + str(title)[:20]),
                        "title": str(title)[:500],
                        "organization": str(org)[:200],
                        "state": state,
                        "category": category,
                        "value": int(float(str(value).replace(",","").replace("₹","").strip())) if value else None,
                        "source": name,
                        "source_url": "https://data.gov.in",
                        "status": "active",
                        "deadline": str(deadline)[:10] if deadline else None,
                    })
                    if ok:
                        saved += 1

                time.sleep(1)

            except Exception as e:
                print(f"  {name} error: {e}")
                break

    return saved

# ─── SOURCE 2: GePNIC State RSS Feeds ────────────────────────────────────────
def fetch_gepnic_rss():
    print("\n📌 GePNIC State RSS feeds...")

    states = [
        ("https://hptenders.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Himachal Pradesh"),
        ("https://uktenders.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Uttarakhand"),
        ("https://govtprocurement.delhi.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Delhi"),
        ("https://mptenders.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Madhya Pradesh"),
        ("https://pbtenders.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Punjab"),
        ("https://haryanaeprocurement.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Haryana"),
        ("https://jktenders.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Jammu & Kashmir"),
        ("https://bidder.mse.gov.in/nicgep/app?page=FrontEndRSSTenders&service=page", "Central-MSE"),
    ]

    saved = 0
    for url, state in states:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.text) > 100:
                try:
                    root = ET.fromstring(r.text)
                    items = root.findall(".//item")
                    print(f"  {state}: {len(items)} items")
                    for item in items[:30]:
                        title = item.findtext("title", "").strip()
                        link = item.findtext("link", url).strip()
                        if len(title) < 10:
                            continue
                        ok = save({
                            "tender_id": make_id("GEPNIC" + state + title[:40]),
                            "title": title[:500],
                            "organization": f"{state} Government",
                            "state": state,
                            "category": "government",
                            "source": "GePNIC",
                            "source_url": link,
                            "status": "active",
                        })
                        if ok:
                            saved += 1
                except ET.ParseError:
                    print(f"  {state}: RSS parse error")
            else:
                print(f"  {state}: {r.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"  {state}: {e}")

    return saved

if __name__ == "__main__":
    print("🚀 Smart Tender Scraper v2")
    print("=" * 50)

    t1 = fetch_datagov_paginated()
    t2 = fetch_gepnic_rss()

    total = supabase.table("tenders").select("id", count="exact").execute()
    print("\n" + "=" * 50)
    print(f"✅ data.gov.in: {t1} saved")
    print(f"✅ GePNIC RSS:  {t2} saved")
    print(f"📊 Total in DB: {total.count}")
