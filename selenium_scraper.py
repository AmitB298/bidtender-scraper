from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client
from dotenv import load_dotenv
import os
import hashlib
import time

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:40]

def save_tender(tender):
    try:
        supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ {tender['title'][:60]}")
    except Exception as e:
        print(f"❌ {e}")

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_eprocure():
    print("🔍 Scraping eProcure CPPP...")
    driver = get_driver()
    try:
        driver.get("https://eprocure.gov.in/eprocure/app?page=FrontEndLatestActiveTenders&service=page")
        time.sleep(3)
        rows = driver.find_elements(By.CSS_SELECTOR, "table#table tr")
        print(f"  Found {len(rows)} rows")
        for row in rows[1:30]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 5:
                title = cols[2].text.strip()
                org = cols[1].text.strip()
                deadline = cols[4].text.strip()
                if len(title) > 5:
                    save_tender({
                        "tender_id": make_id(title + org),
                        "title": title[:500],
                        "organization": org[:200],
                        "state": "Central",
                        "category": "government",
                        "source": "CPPP",
                        "source_url": "https://eprocure.gov.in",
                        "status": "active"
                    })
    except Exception as e:
        print(f"❌ eProcure error: {e}")
    finally:
        driver.quit()

def scrape_gem():
    print("🔍 Scraping GeM Portal...")
    driver = get_driver()
    try:
        driver.get("https://bidplus.gem.gov.in/all-bids")
        time.sleep(4)
        cards = driver.find_elements(By.CSS_SELECTOR, ".bid-details-card, .card, tr")
        print(f"  Found {len(cards)} items")
        for card in cards[:30]:
            try:
                title = card.find_element(By.CSS_SELECTOR, "h5, .bid-title, td:nth-child(2)").text.strip()
                if len(title) > 5:
                    save_tender({
                        "tender_id": make_id("GEM-" + title),
                        "title": title[:500],
                        "organization": "GeM Portal",
                        "state": "Central",
                        "category": "government",
                        "source": "GeM",
                        "source_url": "https://bidplus.gem.gov.in",
                        "status": "active"
                    })
            except:
                continue
    except Exception as e:
        print(f"❌ GeM error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🚀 Selenium Scraper Starting...")
    scrape_eprocure()
    scrape_gem()
    print("✅ All done!")