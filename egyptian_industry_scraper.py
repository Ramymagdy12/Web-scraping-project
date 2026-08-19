import os
import sys
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

# Set output encoding to UTF-8 for console messages
sys.stdout.reconfigure(encoding='utf-8')

# Mapping of industry ID to names (for logs and spreadsheets)
INDUSTRY_MAPPING = {
    9: "Cars Industries",
    10: "Food Industries",
    11: "Chemicals Industries",
    12: "Industrial Detergents",
    19: "Medicines & Cosmetics"
}

class EgyptianIndustryScraper:
    def __init__(self, config_path=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if config_path is None:
            self.config_path = os.path.join(script_dir, "config.json")
        else:
            self.config_path = os.path.abspath(config_path)
            
        self.email = "ahmed.medhat@gblease.com"
        self.password = "User@1234"
        self.target_industries = []
        self.output_file = "scraped_companies.xlsx"
        self.delay_between_requests = 1.5  # seconds
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        self.load_config()
        self.existing_records = []
        self.existing_urls = set()
        self.load_existing_data()

    def safe_request(self, method, url, retries=5, backoff=3, **kwargs):
        """Wrapper around requests session to handle timeouts, retries, and rate limits."""
        for attempt in range(retries):
            try:
                if "timeout" not in kwargs:
                    kwargs["timeout"] = 30
                    
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 429:
                    print(f"\n[!] Rate limited (HTTP 429) at {url}. Sleeping for 60 seconds before retrying...")
                    time.sleep(60)
                    continue
                    
                if response.status_code >= 500:
                    print(f"\n[!] Server error ({response.status_code}) at {url}. Retrying in {backoff * (attempt + 1)}s...")
                    time.sleep(backoff * (attempt + 1))
                    continue
                    
                return response
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                wait_time = backoff * (attempt + 1)
                print(f"\n[!] Connection/Timeout error at {url}: {e}. Retrying ({attempt + 1}/{retries}) in {wait_time}s...")
                time.sleep(wait_time)
                
        print(f"\n[-] All {retries} retries failed for: {url}")
        return None

    def load_config(self):
        """Loads credentials and scraping parameters, checking env vars first, then falling back to config.json."""
        self.email = os.environ.get("SCRAPER_EMAIL", "")
        self.password = os.environ.get("SCRAPER_PASSWORD", "")
        self.target_industries = [9, 10, 11, 12, 19]
        output_file = "scraped_companies.xlsx"
        
        # Load from config.json if environment variables are not set
        if not self.email or not self.password:
            if not os.path.exists(self.config_path):
                print(f"[-] Config file {self.config_path} not found and SCRAPER_EMAIL/SCRAPER_PASSWORD not set. Exiting.")
                sys.exit(1)
                
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.email = config.get("email", self.email)
                    self.password = config.get("password", self.password)
                    self.target_industries = config.get("industries", self.target_industries)
                    output_file = config.get("output_file", output_file)
            except Exception as e:
                print(f"[-] Error parsing config.json: {e}")
                sys.exit(1)
                
        # Resolve output file path
        if not os.path.isabs(output_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_file = os.path.join(script_dir, output_file)
        else:
            self.output_file = output_file
            
        # Check for placeholders
        if "your-email" in self.email or "your-password" in self.password:
            print("[!] WARNING: Please update credentials before running.")
    def load_existing_data(self):
        """Loads already scraped data from Excel to support resuming."""
        if os.path.exists(self.output_file):
            try:
                df = pd.read_excel(self.output_file)
                self.existing_records = df.to_dict("records")
                if "Detail Page URL" in df.columns:
                    self.existing_urls = set(df["Detail Page URL"].dropna().tolist())
                print(f"[+] Loaded {len(self.existing_records)} existing records to resume scraping.")
            except Exception as e:
                print(f"[-] Could not load existing Excel file for resuming: {e}")
    def login(self):
        """Authenticates with the website and validates session."""
        print("[*] Switching to English language...")
        self.safe_request("GET", "https://www.egyptianindustry.com/locale/en")
        
        print("[*] Accessing homepage to fetch CSRF token...")
        base_url = "https://www.egyptianindustry.com/"
        try:
            r = self.safe_request("GET", base_url)
            if not r:
                print("[-] Failed to fetch homepage for CSRF token.")
                return False
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Find Laravel CSRF token
            token_input = soup.find("input", {"name": "_token"})
            if not token_input:
                print("[-] Could not find CSRF token on homepage.")
                return False
            
            csrf_token = token_input.get("value")
            print(f"[+] Found CSRF Token: {csrf_token[:8]}...")
            
            # Perform POST login request
            login_url = "https://www.egyptianindustry.com/login"
            payload = {
                "_token": csrf_token,
                "email": self.email,
                "password": self.password,
                "remember": "on"
            }
            
            headers = {
                "Referer": base_url,
                "Origin": "https://www.egyptianindustry.com"
            }
            
            print(f"[*] Submitting login credentials for: {self.email}")
            response = self.safe_request("POST", login_url, data=payload, headers=headers)
            if not response:
                print("[-] Login POST request failed.")
                return False
            
            # Check login success by inspecting a protected resource or checking cookies
            # We will fetch a company page known to be blocked to see if data is unlocked
            test_co_url = "https://www.egyptianindustry.com/SearchR/1/Page/1/Co/13449/المجموعة-الهندسية-إنشاءات-حمامات-سباحة-وحدات-معالجة-مياه"
            test_r = self.safe_request("GET", test_co_url)
            if not test_r:
                print("[-] Failed to fetch verification company page.")
                return False
            test_soup = BeautifulSoup(test_r.text, "html.parser")
            
            if "Subscribe to access the data" in test_soup.text or "إشترك للحصول على كامل بيانات" in test_soup.text:
                print("[-] Login failed or your account does not have a subscription to view full data.")
                print("[-] Proceeding in anonymous mode (some contact numbers/emails will be hidden).")
                return False
            else:
                print("[+] Successfully logged in! Detailed contact information is unlocked.")
                return True
                
        except Exception as e:
            print(f"[-] Login process failed: {e}")
            print("[-] Running in anonymous mode...")
            return False

    def parse_address_block(self, address_tag):
        """Parses key-value data inside <address> tags where keys are in <span>."""
        data = {}
        if not address_tag:
            return data
            
        spans = address_tag.find_all("span", class_="btn")
        for span in spans:
            key = span.text.strip().replace(":", "").strip()
            
            # Collect following sibling text/links up to next span or br tag
            val_parts = []
            sibling = span.next_sibling
            while sibling:
                if sibling.name in ["span", "br"]:
                    break
                if isinstance(sibling, str):
                    val_parts.append(sibling)
                elif sibling.name == "a":
                    val_parts.append(sibling.text)
                sibling = sibling.next_sibling
                
            value = " ".join("".join(val_parts).strip().split())
            value = value.strip(",/ ").strip()
            data[key] = value
        return data

    def scrape_company_details(self, url):
        """Requests and parses details of a single company page."""
        details = {
            "Activity": "",
            "Factory Address": "",
            "Mobile": "",
            "E-mail": "",
            "General Manager": "",
            "Management Phone": "",
            "Factory Phone": "",
            "Website": "",
            "Fax": "",
            "Management Address": ""
        }
        
        try:
            time.sleep(self.delay_between_requests)
            r = self.safe_request("GET", url)
            if not r or r.status_code != 200:
                status = r.status_code if r else "No Response"
                print(f"  [!] Failed to load company page: {url} (Status: {status})")
                return details
            r.encoding = "utf-8"
                
            soup = BeautifulSoup(r.text, "html.parser")
            address_block = soup.find("address")
            if address_block:
                parsed_data = self.parse_address_block(address_block)
                for k, v in parsed_data.items():
                    if k in details:
                        details[k] = v
                    else:
                        details[k] = v  # Store custom keys if found
            return details
            
        except Exception as e:
            print(f"  [!] Error parsing company details at {url}: {e}")
            return details

    def scrape_all(self):
        """Executes the complete scraping workflow across all configured industries."""
        self.login()
        
        all_companies = self.existing_records
        existing_urls = self.existing_urls
        
        for ind_id in self.target_industries:
            ind_name = INDUSTRY_MAPPING.get(ind_id, f"Industry ID {ind_id}")
            print(f"\n==========================================")
            print(f"[*] Starting Scrape for: {ind_name}")
            print(f"==========================================")
            
            page = 1
            while True:
                url = f"https://www.egyptianindustry.com/SearchR/1/Page/1/Zone/0/Industry/{ind_id}?page={page}"
                print(f"[*] Scraping Page {page}: {url}")
                
                try:
                    time.sleep(self.delay_between_requests)
                    r = self.safe_request("GET", url)
                    if not r:
                        print(f"[-] Could not load page {page} due to connection/timeout errors. Skipping this page.")
                        break
                    r.encoding = "utf-8"
                    
                    if r.status_code == 404:
                        print(f"[*] Page {page} returned 404. Reached end of industry listings.")
                        break
                        
                    soup = BeautifulSoup(r.text, "html.parser")
                    listings = soup.find_all("div", class_="f-listings-item")
                    
                    if not listings:
                        print(f"[*] No listings found on page {page}. Reached end of industry listings.")
                        break
                        
                    print(f"[+] Found {len(listings)} companies on page {page}.")
                    
                    for idx, listing in enumerate(listings, 1):
                        # Extract company name and URL
                        title_el = listing.find("h1", class_="f-listings-item__title")
                        if not title_el or not title_el.find("a"):
                            continue
                            
                        co_name = title_el.find("a").text.strip()
                        co_url = title_el.find("a")["href"]
                        co_url = urljoin("https://www.egyptianindustry.com/", co_url)
                        
                        if co_url in existing_urls:
                            print(f"  ({idx}/{len(listings)}) Skipping (Already Scraped): {co_name[:40]}...")
                            continue
                        
                        # Extract classification / city if available
                        city = ""
                        class_span = listing.find("div", class_="listing-single__content")
                        if class_span:
                            city_text = class_span.text.strip()
                            if "Categories :" in city_text:
                                city = city_text.replace("Categories :", "").strip()
                                city = " ".join(city.split())
                            elif "التصنيفات :" in city_text:
                                city = city_text.replace("التصنيفات :", "").strip()
                                city = " ".join(city.split())
                        
                        print(f"  ({idx}/{len(listings)}) Scrape Details: {co_name[:40]}...")
                        
                        # Get detailed contact information from company page
                        co_details = self.scrape_company_details(co_url)
                        
                        company_info = {
                            "Company Name": co_name,
                            "Industry": ind_name,
                            "City/Classification": city,
                            "Detail Page URL": co_url,
                            **co_details
                        }
                        all_companies.append(company_info)
                        existing_urls.add(co_url)
                    
                    # Page completed, auto-save data to prevent loss
                    self.save_to_excel(all_companies)
                    
                    page += 1
                    
                except Exception as e:
                    print(f"[-] Error during page {page} scrape: {e}")
                    break
                    
        print(f"\n[+] Scraping finished! Total companies collected: {len(all_companies)}")
        self.save_to_excel(all_companies)

    def save_to_excel(self, data):
        """Saves current data to configured Excel spreadsheet."""
        if not data:
            return
        try:
            df = pd.DataFrame(data)
            # Reorder columns to be logical and user-friendly
            col_order = [
                "Company Name",
                "Industry",
                "City/Classification",
                "Activity",
                "General Manager",
                "Mobile",
                "E-mail",
                "Management Phone",
                "Factory Phone",
                "Website",
                "Factory Address",
                "Management Address",
                "Fax",
                "Detail Page URL"
            ]
            # Handle any extra keys
            for col in df.columns:
                if col not in col_order:
                    col_order.append(col)
                    
            df = df.reindex(columns=[c for c in col_order if c in df.columns])
            df.to_excel(self.output_file, index=False)
            print(f"[+] Saved {len(data)} records to {self.output_file}")
        except Exception as e:
            print(f"[-] Failed to save to Excel: {e}")

if __name__ == "__main__":
    # Configure logging to both console and a log file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "scraper_run.log")
    
    # Write start marker to log
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n=========================================\n")
        log_file.write(f"Scraper Run Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"=========================================\n")
        
    class DualOutput:
        def __init__(self, terminal, file_path):
            self.terminal = terminal
            self.log_file = open(file_path, "a", encoding="utf-8")
            
        def write(self, message):
            self.terminal.write(message)
            self.log_file.write(message)
            self.log_file.flush()
            
        def flush(self):
            self.terminal.flush()
            self.log_file.flush()
            
    # Redirect standard output and errors
    sys.stdout = DualOutput(sys.stdout, log_path)
    sys.stderr = DualOutput(sys.stderr, log_path)
    
    try:
        scraper = EgyptianIndustryScraper()
        scraper.scrape_all()
        print(f"\n[+] Scraper Run Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"\n[-] Critical error during scraper run: {e}")
        import traceback
        traceback.print_exc()
