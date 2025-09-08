#!/usr/bin/env python3
import csv
import json
import re
import time
import sys
from typing import Optional, Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tqdm import tqdm

# ---------- Config ----------
URL = "https://www.framesdirect.com/eyeglasses/"
HEADLESS = True
TIMEOUT = 15
OUTPUT_CSV = "framesdirect_output.csv"
OUTPUT_JSON = "framesdirect_output.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
)

# ---------- Helpers ----------
_price_re = re.compile(r"(\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)")

def extract_number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    text = text.replace("\xa0", " ").strip()
    m = _price_re.search(text)
    if not m:
        return None
    normalized = m.group(1).replace(",", "").replace(" ", "")
    try:
        return float(normalized)
    except ValueError:
        return None

def safe_text(bs_elem) -> Optional[str]:
    return bs_elem.get_text(strip=True) if bs_elem else None

# ---------- Main scraping function ----------
def scrape_framesdirect(url: str) -> List[Dict]:
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    products = []

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        print(f"[ERROR] Could not start Chrome driver: {e}", file=sys.stderr)
        if driver:
            driver.quit()
        raise

    try:
        print(f"[INFO] Visiting {url}")
        driver.get(url)

        try:
            WDW(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "prod-holder"))
            )
            print("[INFO] Product tiles detected.")
        except TimeoutException:
            print("[WARN] prod-holder not found within timeout; trying prod-title selector.")
            try:
                WDW(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "prod-title"))
                )
                print("[INFO] prod-title detected.")
            except TimeoutException:
                print("[ERROR] No product tiles found. Exiting.")
                return []

        time.sleep(1.0)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "lxml")

        container_selectors = [
            ("div", {"class": "prod-holder"}),
            ("div", {"class": "prod-item"}),
            ("div", {"class": "prod-title prod-model"}),
            ("div", {"class": "prod-title"}),
        ]

        product_tiles = []
        for tag, attrs in container_selectors:
            found = soup.find_all(tag, attrs=attrs)
            if found:
                product_tiles = found
                print(f"[INFO] Found {len(product_tiles)} product tiles using selector {attrs}.")
                break

        if not product_tiles:
            product_tiles = soup.select("div[class*='prod']")
            print(f"[WARN] Fallback selector found {len(product_tiles)} candidate tiles.")

        for tile in tqdm(product_tiles, desc="Extracting products"):
            brand_tag = tile.find(lambda t: t.name == "div" and ("catalog-container" in (t.get("class") or []) or "catalog-name" in (t.get("class") or [])))
            brand = safe_text(brand_tag) or None

            name_tag = tile.find("div", class_="product_name") \
                       or tile.find("div", class_="prod-model") \
                       or tile.find("a", class_="prod-title-link")
            name = safe_text(name_tag) or None

            price_block = tile.find("div", class_="prod-catalog-retail-price") \
                        or tile.find("div", class_="prod-price-wrap") \
                        or tile.find("div", class_="prod-price")

            if price_block:
                original_tag = price_block.find("div", class_="prod-aslowas") \
                               or price_block.find("span", class_="was-price") \
                               or price_block.find(lambda e: e.name in ["span", "div"] and ("was" in " ".join(e.get("class") or []) or "orig" in " ".join(e.get("class") or [])))
                current_tag = price_block.find("div", class_="product-offer-price") \
                              or price_block.find("span", class_="now-price") \
                              or price_block.find("div", class_="prod-aslowas")

                original_price = extract_number(safe_text(original_tag))
                current_price = extract_number(safe_text(current_tag))
            else:
                original_price = current_price = None

            discount_tag = tile.find("div", class_="frame-discount") \
                           or tile.find(lambda e: e.name in ["div", "span"] and "%" in (e.get_text() or ""))
            discount = safe_text(discount_tag)

            if discount:
                m = re.search(r"\d{1,3}\s*%+", discount)
                discount = m.group(0) if m else discount.strip()
            else:
                discount = None

            product = {
                "Brand": brand,
                "Product_Name": name,
                "Original_Price": original_price,
                "Current_Price": current_price,
                "Discount": discount,
            }
            products.append(product)

        print(f"[INFO] Extracted {len(products)} product records (may include None values).")
        return products

    finally:
        if driver:
            driver.quit()
            print("[INFO] Browser closed.")

# ---------- Save functions ----------
def save_csv(records: List[Dict], path: str):
    if not records:
        print("[WARN] No records to save to CSV.")
        return
    
    # fixed header order
    headers = ["Brand", "Product_Name", "Original_Price", "Current_Price", "Discount"]

    # convert None -> "null" for CSV only
    converted_records = [
        {k: ("null" if v is None else v) for k, v in r.items()}
        for r in records
    ]

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in converted_records:
            writer.writerow(row)
    print(f"[INFO] Saved CSV to {path}")

def save_json(records: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved JSON to {path}")

# ---------- Main ----------
if __name__ == "__main__":
    out = scrape_framesdirect(URL)
    save_csv(out, OUTPUT_CSV)   # CSV gets "null"
    save_json(out, OUTPUT_JSON) # JSON gets null
    print("Done.")
