import re, json, requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0"}

def parse_listing(category_url: str):
    resp = requests.get(category_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    products = []
    for card in soup.select("div.ProductCardstyles__Wrapper"):
        title_el = card.select_one("a.Linkstyles__Link")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = urljoin(category_url, title_el["href"])
        price_txt = card.select_one(".Pricestyles__Price").get_text()
        current = float(price_txt.replace("CHF", "").replace(" ", "").strip())
        rating_el = card.select_one(".Ratingstyles__Stars")
        rating = float(rating_el["aria-label"].split()[0]) if rating_el else None
        reviews_el = card.select_one(".Ratingstyles__Count")
        reviews = int(re.sub(r"[()]", "", reviews_el.get_text())) if reviews_el else 0
        products.append((title, link, current, rating, reviews))
    return products

def fetch_baseline_price(product_url: str, days: int = 30):
    resp = requests.get(product_url, headers=HEADERS)
    resp.raise_for_status()
    # Use correct regex to find the price history JSON
    match = re.search(r"window\.__PRICE_HISTORY__\s*=\s*({.+?});", resp.text)
    if not match:
        raise RuntimeError("Could not find price history JSON.")
    history = json.loads(match.group(1))
    cutoff = datetime.utcnow() - timedelta(days=days)
    prices = [entry["price"] for entry in history.get("data", [])
              if datetime.fromisoformat(entry["date"]) >= cutoff]
    if not prices:
        raise RuntimeError(f"No price data in the last {days} days.")
    return min(prices)

def find_big_drops(
    category_url: str,
    min_rating: float = 4.0,
    min_reviews: int = 50,
    drop_threshold: float = 30.0,
    baseline_days: int = 30
):
    """
    Scan the given Galaxus category URL for items whose price has
    dropped by at least drop_threshold% compared to the minimum
    in the last baseline_days.
    Filters out items below min_rating or min_reviews.
    Returns a list of dicts with title, url, baseline, current, drop_pct.
    """
    alerts = []
    for title, link, current, rating, reviews in parse_listing(category_url):
        if rating is None or rating < min_rating or reviews < min_reviews:
            continue
        try:
            baseline = fetch_baseline_price(link, days=baseline_days)
        except Exception:
            continue
        raw_pct = (baseline - current) / baseline * 100
        drop_pct = abs(raw_pct)
        if drop_pct >= drop_threshold:
            alerts.append({
                "title": title,
                "url": link,
                "baseline": baseline,
                "current": current,
                "drop_pct": round(drop_pct, 1),
            })

    return alerts
