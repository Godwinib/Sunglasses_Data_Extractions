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
BASE_URL = "https://www.framesdirect.com/eyeglasses/"
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
def scrape_page(url: str) -> List[Dict]:
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
        except TimeoutException:
            try:
                WDW(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "prod-title"))
                )
            except TimeoutException:
                print("[ERROR] No product tiles found on this page.")
                return []

        time.sleep(1.0)
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
                break

        if not product_tiles:
            product_tiles = soup.select("div[class*='prod']")

        for tile in product_tiles:
            brand_tag = tile.find(lambda t: t.name == "div" and ("catalog-container" in (t.get("class") or []) or "catalog-name" in (t.get("class") or [])))
            brand = safe_text(brand_tag)

            name_tag = tile.find("div", class_="product_name") \
                       or tile.find("div", class_="prod-model") \
                       or tile.find("a", class_="prod-title-link")
            name = safe_text(name_tag)

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

            products.append({
                "Brand": brand,
                "Product_Name": name,
                "Original_Price": original_price,
                "Current_Price": current_price,
                "Discount": discount,
            })

        print(f"[INFO] Extracted {len(products)} products from {url}")
        return products

    finally:
        if driver:
            driver.quit()

# ---------- Save functions ----------
def save_csv(records: List[Dict], path: str):
    if not records:
        print("[WARN] No records to save to CSV.")
        return
    headers = ["Brand", "Product_Name", "Original_Price", "Current_Price", "Discount"]
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
    all_records = []
    for page in range(1, 100):  # Pages 1 to 99
        page_url = f"{BASE_URL}?page={page}"
        records = scrape_page(page_url)
        if not records:  # stop if no products found
            print(f"[WARN] No products on page {page}, stopping early.")
            break
        all_records.extend(records)
        time.sleep(2)  # be polite

    save_csv(all_records, OUTPUT_CSV)
    save_json(all_records, OUTPUT_JSON)
    print(f"[INFO] Finished scraping. Total products: {len(all_records)}")
