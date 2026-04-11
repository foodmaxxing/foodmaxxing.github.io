#!/usr/bin/env python3
“””
FoodMaxxing Price Scraper
Runs twice a week, pulls menu prices, updates prices.json, pushes to GitHub Pages.
“””

import json
import os
import re
import time
import random
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── CONFIG ───────────────────────────────────────────────────────────────────

REPO_DIR    = Path.home() / “foodmaxxing”
DATA_FILE   = REPO_DIR / “data” / “prices.json”
LOG_FILE    = Path.home() / “foodmaxxing_scraper.log”
GITHUB_REPO = “https://github.com/foodmaxxing/foodmaxxing.github.io.git”

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s [%(levelname)s] %(message)s”,
handlers=[
logging.FileHandler(LOG_FILE),
logging.StreamHandler(),
]
)
log = logging.getLogger(**name**)

HEADERS = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36”,
“Accept-Language”: “en-US,en;q=0.9”,
“Accept”: “text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8”,
}

# ─── SOURCES ──────────────────────────────────────────────────────────────────

# Maps chain key -> PriceListo URL for that chain

PRICELISTO_URLS = {
“mcdonalds”:  “https://www.pricelisto.com/fast-food-prices/mcdonalds-menu-prices”,
“chipotle”:   “https://www.pricelisto.com/fast-food-prices/chipotle-menu-prices”,
“tacobell”:   “https://www.pricelisto.com/fast-food-prices/taco-bell-menu-prices”,
“wendys”:     “https://www.pricelisto.com/fast-food-prices/wendys-menu-prices”,
“burgerking”: “https://www.pricelisto.com/fast-food-prices/burger-king-menu-prices”,
“chickfila”:  “https://www.pricelisto.com/fast-food-prices/chick-fil-a-menu-prices”,
“starbucks”:  “https://www.pricelisto.com/coffee-shop-prices/starbucks-menu-prices”,
“dominos”:    “https://www.pricelisto.com/fast-food-prices/dominos-pizza-menu-prices”,
“panera”:     “https://www.pricelisto.com/fast-food-prices/panera-bread-menu-prices”,
“subway”:     “https://www.pricelisto.com/fast-food-prices/subway-menu-prices”,
}

# Items we specifically want to track per chain

TRACKED_ITEMS = {
“mcdonalds”:  [“Big Mac”, “Medium Fries”, “McChicken”],
“chipotle”:   [“Chicken Burrito”, “Chicken Bowl”, “Chips & Guac”],
“tacobell”:   [“Crunchy Taco”, “Chalupa Supreme”, “Beef Burrito”],
“wendys”:     [“Dave’s Single”, “Frosty (Small)”, “Baconator”],
“burgerking”: [“Whopper”, “Chicken Fries”, “Impossible Whopper”],
“chickfila”:  [“Chicken Sandwich”, “Waffle Fries (Med)”, “Nuggets (8pc)”],
“starbucks”:  [“Grande Latte”, “Grande Frappuccino”, “Cheese Danish”],
“dominos”:    [“Large Pepperoni”, “Medium Cheese”, “Breadsticks (8pc)”],
“panera”:     [“Broccoli Cheddar Soup”, “Turkey Sandwich”, “Bagel”],
“subway”:     [“Footlong Italian BMT”, “6-inch Turkey”, “Cookie”],
}

# ─── SCRAPER ──────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> BeautifulSoup | None:
“”“Fetch a page and return BeautifulSoup object.”””
try:
time.sleep(random.uniform(2, 5))
r = requests.get(url, headers=HEADERS, timeout=20)
r.raise_for_status()
return BeautifulSoup(r.text, “html.parser”)
except Exception as e:
log.warning(f”Failed to fetch {url}: {e}”)
return None

def extract_price(text: str) -> float | None:
“”“Extract a dollar price from a string.”””
match = re.search(r’$\s*([\d,]+.?\d*)’, text)
if match:
return float(match.group(1).replace(”,”, “”))
return None

def scrape_pricelisto(chain_key: str) -> dict:
“””
Scrape current prices from PriceListo for a given chain.
Returns dict of {item_name: price}.
“””
url = PRICELISTO_URLS.get(chain_key)
if not url:
return {}

```
soup = fetch_page(url)
if not soup:
    return {}

prices = {}
tracked = TRACKED_ITEMS.get(chain_key, [])

# PriceListo uses table rows with item name + price columns
rows = soup.find_all("tr")
for row in rows:
    cells = row.find_all(["td", "th"])
    if len(cells) >= 2:
        name_text = cells[0].get_text(strip=True)
        price_text = cells[-1].get_text(strip=True)
        price = extract_price(price_text)
        if price:
            # Fuzzy match against our tracked items
            for tracked_name in tracked:
                if tracked_name.lower() in name_text.lower() or name_text.lower() in tracked_name.lower():
                    prices[tracked_name] = price
                    break

log.info(f"  {chain_key}: scraped {len(prices)}/{len(tracked)} items")
return prices
```

def scrape_fastfoodmenuprices(chain_key: str) -> dict:
“””
Fallback scraper using fastfoodmenuprices.com
“””
chain_slugs = {
“mcdonalds”:  “mcdonalds”,
“chipotle”:   “chipotle”,
“tacobell”:   “taco-bell”,
“wendys”:     “wendys”,
“burgerking”: “burger-king”,
“chickfila”:  “chick-fil-a”,
“starbucks”:  “starbucks”,
“dominos”:    “dominos-pizza”,
“panera”:     “panera-bread”,
“subway”:     “subway”,
}

```
slug = chain_slugs.get(chain_key)
if not slug:
    return {}

url = f"https://www.fastfoodmenuprices.com/{slug}-menu-prices/"
soup = fetch_page(url)
if not soup:
    return {}

prices = {}
tracked = TRACKED_ITEMS.get(chain_key, [])

# Look for table rows or dt/dd pairs
rows = soup.find_all("tr")
for row in rows:
    cells = row.find_all(["td", "th"])
    if len(cells) >= 2:
        name_text = cells[0].get_text(strip=True)
        price_text = " ".join(c.get_text(strip=True) for c in cells[1:])
        price = extract_price(price_text)
        if price:
            for tracked_name in tracked:
                if tracked_name.lower() in name_text.lower():
                    prices[tracked_name] = price
                    break

return prices
```

# ─── DATA MANAGEMENT ──────────────────────────────────────────────────────────

def load_data() -> dict:
with open(DATA_FILE, “r”) as f:
return json.load(f)

def save_data(data: dict):
with open(DATA_FILE, “w”) as f:
json.dump(data, f, indent=2)
log.info(f”Saved data to {DATA_FILE}”)

def update_prices(data: dict, chain_key: str, new_prices: dict) -> int:
“””
Add today’s prices to the historical data for a chain.
Only adds a new entry if the price has actually changed.
Returns count of items updated.
“””
today = datetime.now().strftime(”%Y-%m-%d”)
chain = data[“chains”].get(chain_key)
if not chain:
log.warning(f”Chain {chain_key} not found in data”)
return 0

```
updated = 0
for item_name, new_price in new_prices.items():
    if item_name not in chain["items"]:
        # New item — initialize
        chain["items"][item_name] = [{"date": today, "price": new_price}]
        updated += 1
        log.info(f"  New item: {chain['name']} / {item_name} = ${new_price}")
        continue

    history = chain["items"][item_name]
    last_price = history[-1]["price"]

    if abs(new_price - last_price) >= 0.01:
        history.append({"date": today, "price": new_price})
        updated += 1
        direction = "↑" if new_price > last_price else "↓"
        log.info(f"  {direction} Price change: {chain['name']} / {item_name}: ${last_price} → ${new_price}")
    else:
        log.info(f"  No change: {chain['name']} / {item_name} = ${new_price}")

return updated
```

# ─── GIT DEPLOY ───────────────────────────────────────────────────────────────

def git_push(message: str):
“”“Commit and push changes to GitHub Pages.”””
try:
subprocess.run([“git”, “-C”, str(REPO_DIR), “add”, “.”], check=True)
subprocess.run([“git”, “-C”, str(REPO_DIR), “commit”, “-m”, message], check=True)
subprocess.run([“git”, “-C”, str(REPO_DIR), “push”], check=True)
log.info(“Pushed to GitHub Pages”)
except subprocess.CalledProcessError as e:
log.error(f”Git push failed: {e}”)

# ─── MAIN SWEEP ───────────────────────────────────────────────────────────────

def run_sweep():
log.info(”=” * 50)
log.info(“FoodMaxxing Scraper — starting sweep”)
log.info(”=” * 50)

```
data = load_data()
today = datetime.now().strftime("%Y-%m-%d")
total_updated = 0

for chain_key in TRACKED_ITEMS.keys():
    log.info(f"Scraping: {chain_key}")

    # Try PriceListo first
    prices = scrape_pricelisto(chain_key)

    # Fallback to fastfoodmenuprices if we got less than half the items
    tracked_count = len(TRACKED_ITEMS[chain_key])
    if len(prices) < tracked_count // 2:
        log.info(f"  PriceListo gave {len(prices)}/{tracked_count} — trying fallback")
        fallback = scrape_fastfoodmenuprices(chain_key)
        # Merge, preferring primary source
        for k, v in fallback.items():
            if k not in prices:
                prices[k] = v

    if prices:
        count = update_prices(data, chain_key, prices)
        total_updated += count
    else:
        log.warning(f"  No prices scraped for {chain_key}")

    # Polite delay between chains
    time.sleep(random.uniform(3, 7))

# Update timestamp
data["last_updated"] = today
save_data(data)

log.info(f"Sweep complete. {total_updated} price updates recorded.")

# Push to GitHub
if total_updated > 0:
    git_push(f"Price update {today} — {total_updated} changes")
else:
    log.info("No price changes detected — skipping git push")
```

if **name** == “**main**”:
run_sweep()
