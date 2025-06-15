import json
import pytest
from datetime import datetime, timedelta
from tools.galaxus import parse_listing, fetch_baseline_price, find_big_drops

# A simple HTML snippet mocking one product card:
SAMPLE_LISTING_HTML = """
<div class="ProductCardstyles__Wrapper">
  <a class="Linkstyles__Link" href="/de/p/printest-123">Test Notebook</a>
  <div class="Pricestyles__Price">CHF 500.00</div>
  <div class="Ratingstyles__Stars" aria-label="4.5 out of 5 stars"></div>
  <div class="Ratingstyles__Count">(150)</div>
</div>
"""

# A minimal price-history JSON mock embedded on a product page:
SAMPLE_HISTORY_JSON = {
    "data": [
        {"date": (datetime.utcnow() - timedelta(days=10)).isoformat(), "price": 600},
        {"date": (datetime.utcnow() - timedelta(days=5)).isoformat(),  "price": 450},
        {"date": (datetime.utcnow() - timedelta(days=1)).isoformat(),  "price": 500},
    ]
}
SAMPLE_PRODUCT_HTML = f"""
<script>
  window.__PRICE_HISTORY__ = {json.dumps(SAMPLE_HISTORY_JSON)};
</script>
"""

class DummyResponse:
    def __init__(self, text):
        self.text = text
    def raise_for_status(self):
        pass

@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    import requests
    def fake_get(url, headers=None):
        if "producttype" in url:
            return DummyResponse(SAMPLE_LISTING_HTML)
        else:
            return DummyResponse(SAMPLE_PRODUCT_HTML)
    monkeypatch.setattr(requests, "get", fake_get)

def test_parse_listing_returns_expected_tuple():
    items = parse_listing("https://galaxus.ch/de/s1/producttype/notebook-6")
    assert len(items) == 1
    title, link, price, rating, reviews = items[0]
    assert title == "Test Notebook"
    assert "printest-123" in link
    assert price == 500.0
    assert rating == 4.5
    assert reviews == 150

def test_find_big_drops_filters_no_drop_for_high_threshold():
    # With a 15% threshold, our sample drop (~11.1%) should be filtered out:
    results = find_big_drops(
        "https://galaxus.ch/de/s1/producttype/notebook-6",
        min_rating=4.0,
        min_reviews=100,
        drop_threshold=15.0,
        baseline_days=30
    )
    assert results == []

def test_find_big_drops_detects_drop_for_lower_threshold():
    # Lower the threshold to 10% so our ~11.1% drop triggers:
    results = find_big_drops(
        "https://galaxus.ch/de/s1/producttype/notebook-6",
        min_rating=4.0,
        min_reviews=100,
        drop_threshold=10.0,
        baseline_days=30
    )
    assert len(results) == 1
    drop = results[0]
    assert drop["title"] == "Test Notebook"
    assert drop["baseline"] == 450
    assert drop["current"] == 500
    # (450 - 500) / 450 * 100 = -11.11 → drop_pct = 11.1%
    assert drop["drop_pct"] == 11.1
