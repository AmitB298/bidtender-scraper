import requests
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os
import time
import random
from datetime import datetime, timedelta

load_dotenv()

# Supabase connect
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def save_tender(tender):
    try:
        result = supabase.table("tenders").upsert(tender, on_conflict="tender_id").execute()
        print(f"✅ Saved: {tender['title'][:50]}")
    except Exception as e:
        print(f"❌ Error: {e}")

def scrape_cppp():
    print("🔍 Scraping CPPP...")
    url = "https://eprocure.gov.in/eprocure/app?page=FrontEndTendersByOrganisation&service=page"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr")[1:20]
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 4:
                tender = {
                    "tender_id": f"CPPP-{cols[0].text.strip()[:50]}",
                    "title": cols[1].text.strip()[:500],
                    "organization": cols[2].text.strip()[:200],
                    "state": "Central",
                    "category": "government",
                    "source": "CPPP",
                    "source_url": url,
                    "status": "active"
                }
                if tender["title"]:
                    save_tender(tender)
    except Exception as e:
        print(f"CPPP Error: {e}")

def generate_sample_tenders():
    """Real jaise sample tenders — jab tak scraping setup ho"""
    print("📦 Adding sample India tenders...")
    
    states = ["Uttar Pradesh", "Maharashtra", "Gujarat", "Rajasthan", "Madhya Pradesh",
              "Karnataka", "Tamil Nadu", "West Bengal", "Bihar", "Punjab",
              "Haryana", "Andhra Pradesh", "Telangana", "Kerala", "Odisha"]
    
    categories = ["construction", "it", "healthcare", "education", "defense", "infrastructure"]
    
    orgs = [
        "PWD UP", "NHAI", "Railways Ministry", "CPWD", "BRO",
        "Municipal Corporation Mumbai", "BESCOM Karnataka", "BSNL",
        "RITES Ltd", "NBCC India", "IRCON International", "HAL",
        "DRDO", "ISRO", "Ministry of Health", "Ministry of Education",
        "Smart Cities Mission", "Jal Jeevan Mission", "PM Awas Yojana"
    ]
    
    titles = [
        "Construction of 4-Lane Highway from {} to {}",
        "Supply of Medical Equipment to District Hospital {}",
        "Development of Smart City Infrastructure in {}",
        "Installation of Solar Power Plant {} MW",
        "Construction of Government School Building",
        "Supply and Installation of IT Equipment",
        "Development of Mobile App for {} Department",
        "Construction of Water Supply Pipeline",
        "Renovation of Government Office Building",
        "Supply of Ambulances to {} District",
        "Construction of Bridge over River",
        "Installation of CCTV Surveillance System",
        "Construction of Affordable Housing Units",
        "Supply of Laboratory Equipment",
        "Development of E-Governance Portal"
    ]
    
    cities = ["Lucknow", "Mumbai", "Delhi", "Pune", "Jaipur", "Bengaluru", 
              "Chennai", "Kolkata", "Patna", "Chandigarh"]
    
    tenders = []
    for i in range(100):
        state = random.choice(states)
        city1 = random.choice(cities)
        city2 = random.choice(cities)
        title_template = random.choice(titles)
        title = title_template.format(city1, city2) if "{}" in title_template else title_template
        
        deadline = datetime.now() + timedelta(days=random.randint(5, 90))
        value = random.randint(500000, 500000000)
        
        tender = {
            "tender_id": f"SAMPLE-{i+1:04d}-{random.randint(1000,9999)}",
            "title": title,
            "organization": random.choice(orgs),
            "state": state,
            "category": random.choice(categories),
            "value": value,
            "deadline": deadline.strftime("%Y-%m-%d"),
            "source": "Sample Data",
            "source_url": "https://eprocure.gov.in",
            "location": f"{city1}, {state}",
            "description": f"Tender for {title} in {state}. Value: Rs {value:,}. Deadline: {deadline.strftime('%d %b %Y')}",
            "status": "active"
        }
        tenders.append(tender)
    
    for t in tenders:
        save_tender(t)
    
    print(f"✅ {len(tenders)} sample tenders added!")

if __name__ == "__main__":
    print("🚀 BidTenderAssist Scraper Starting...")
    generate_sample_tenders()
    scrape_cppp()
    print("✅ Done!")