import os
import re
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

# Corrected Domain URLs
ICICI_URL = "https://www.icicibank.com/corporate/global-markets/forex/forex-card-rate"
HDFC_BASE_URL = "https://www.hdfcbank.com/personal/resources/rates"

def get_ist_time_and_window():
    """
    Returns the current date string and determines the target execution window.
    Handles GitHub cron delays by checking which schedule slot the current time is closest to.
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    date_str = now.strftime("%Y-%m-%d")
    
    # Check current hour to assign the file name to the correct shift window
    # If GitHub runs the 10:30 AM job up to 2 hours late, it still records as 10 am.
    if 8 <= now.hour < 14:
        time_str = "10 am"
    else:
        time_str = "04 pm"
        
    return date_str, time_str

def get_browser_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

def archive_icici(date_str, time_str):
    try:
        response = requests.get(ICICI_URL, headers=get_browser_headers(), timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = f"# ICICI Forex Rates - {date_str} {time_str}\n\n"
        
        tables = soup.find_all('table')
        if tables:
            for i, table in enumerate(tables):
                content += f"### Rate Table {i+1}\n"
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        content += "| " + " | ".join(cells) + " |\n"
                content += "\n"
        else:
            content += soup.get_text(separator="\n", strip=True)

        os.makedirs(f"icici/{date_str}", exist_ok=True)
        filename = f"icici/{date_str}/rates_{time_str.replace(' ', '_')}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully archived ICICI rates to {filename}")
    except Exception as e:
        print(f"Error archiving ICICI: {e}")

def archive_hdfc(date_str, time_str):
    try:
        # Step 1: Hit HDFC's main rate landing page to locate the dynamic PDF endpoint
        session = requests.Session()
        landing_response = session.get(HDFC_BASE_URL, headers=get_browser_headers(), timeout=15)
        landing_response.raise_for_status()
        
        soup = BeautifulSoup(landing_response.text, 'html.parser')
        pdf_url = None
        
        # Look for links targeting dynamic content-streams matching their document repository patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "contentstream-id" in href or "forex" in href.lower() and href.endswith('.pdf'):
                pdf_url = href
                if not pdf_url.startswith("http"):
                    pdf_url = "https://www.hdfcbank.com" + pdf_url
                break
        
        if not pdf_url:
            # Fallback regex matching string fallback if layout shifts slightly
            match = re.search(r'(https://www\.hdfcbank\.com/content/api/contentstream-id/[^\s"\']+)', landing_response.text)
            if match:
                pdf_url = match.group(1)
                
        if not pdf_url:
            raise Exception("Could not discover HDFC's dynamic Forex PDF link on their index page.")
            
        # Step 2: Download the extracted dynamic PDF link target
        pdf_response = session.get(pdf_url, headers=get_browser_headers(), timeout=20)
        pdf_response.raise_for_status()
        
        os.makedirs(f"hdfc/{date_str}", exist_ok=True)
        filename = f"hdfc/{date_str}/rates_{time_str.replace(' ', '_')}.pdf"
        
        with open(filename, "wb") as f:
            f.write(pdf_response.content)
        print(f"Successfully archived HDFC rates from dynamic URL to {filename}")
        
    except Exception as e:
        print(f"Error archiving HDFC: {e}")

if __name__ == "__main__":
    date_str, time_str = get_ist_time_and_window()
    print(f"Starting Forex Archiver Execution for window: {date_str} [{time_str}]")
    
    archive_icici(date_str, time_str)
    archive_hdfc(date_str, time_str)
