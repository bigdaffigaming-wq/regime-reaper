import asyncio
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

async def main():
    url = "https://tampa.craigslist.org/search/cto"
    params = {"query": "toyota camry", "purveyor": "owner", "max_price": 2500}

    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        print(f"Status: {resp.status_code}")
        print(f"URL: {resp.url}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Check what result containers exist
    for selector in ["li.cl-search-result", ".result-row", "li[data-pid]", ".cl-search-result"]:
        found = soup.select(selector)
        print(f"  {selector}: {len(found)} found")

    # Print first 500 chars of body to see structure
    body = soup.find("body")
    if body:
        print("\nFirst 1000 chars of body:")
        print(body.get_text()[:1000])

    # Look for any li elements with class
    lis = soup.find_all("li", class_=True)
    if lis:
        print(f"\nAll li classes found: {set(' '.join(li.get('class', [])) for li in lis[:20])}")

asyncio.run(main())
