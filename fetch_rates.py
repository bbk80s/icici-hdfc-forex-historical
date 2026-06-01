import os
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

# Define URLs (Replace with your specific localized/preferred links if necessary)
ICICI_URL = "https://www.icici.bank.in/corporate/global-markets/forex/forex-card-rate"
HDFC_PDF_URL = "https://www.hdfcbank.com/content/api/contentstream-id/723fb80a-2dde-42a3-9793-7ae1be57c87f/416d84a7-8059-45e0-b636-f09b53145410" # Dummy placeholder URL for HDFC's daily changing dynamic link

def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

def archive_icici(date_str, time_str):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(ICICI_URL, headers=headers)
        response.raise_for_status()
        
        # Parse HTML and try to isolate main content tables to keep it highly readable
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Simple extraction strategy: get text or format tables natively
        content = f"# ICICI Forex Rates - {date_str} {time_str}\n\n"
        
        # Find tables and convert them to simple readable markdown text
        tables = soup.find_all('table')
        if tables:
            for i, table in enumerate(tables):
                content += f"### Rate Table {i+1}\n"
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    content += "| " + " | ".join(cells) + " |\n"
                content += "\n"
        else:
            # Fallback if structure changes: Extract pure structured text
            content += soup.get_text(separator="\n", strip=True)

        # Ensure directory exists
        os.makedirs(f"icici/{date_str}", exist_ok=True)
        filename = f"icici/{date_str}/rates_{time_str.replace(' ', '_')}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully archived ICICI rates to {filename}")
    except Exception as e:
        print(f"Error archiving ICICI: {e}")

def archive_hdfc(date_str, time_str):
    try:
        # Note: If HDFC uses a dynamic URL system, you may need a scraper extension 
        # to find the specific daily PDF path from their main forex page.
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(HDFC_PDF_URL, headers=headers)
        response.raise_for_status()
        
        os.makedirs(f"hdfc/{date_str}", exist_ok=True)
        filename = f"hdfc/{date_str}/rates_{time_str.replace(' ', '_')}.pdf"
        
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Successfully archived HDFC rates to {filename}")
    except Exception as e:
        print(f"Error archiving HDFC: {e}")

if __name__ == "__main__":
    now = get_ist_time()
    date_str = now.strftime("%Y-%m-%d")      # Format: 2026-06-01
    time_str = now.strftime("%I %p").lower() # Format: 10 am or 04 pm
    
    archive_icici(date_str, time_str)
    archive_hdfc(date_str, time_str)
