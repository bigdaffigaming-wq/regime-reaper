import re
import httpx
import asyncio
from typing import Optional
from bs4 import BeautifulSoup

from app.adapters.base import SourceAdapter, NormalizedListing, SearchParams
from app.core.logging import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

SAPI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# City name → (craigslist subdomain, area_id)
# Area IDs used in sapi batch parameter — format: {areaId}-0-360-0-0
CITY_MAP = {
    "tampa": ("tampa", 37),
    "miami": ("miami", 35),
    "orlando": ("orlando", 39),
    "jacksonville": ("jacksonville", 26),
    "fort lauderdale": ("fortlauderdale", 22),
    "west palm beach": ("westpalmbeach", 55),
    "sarasota": ("sarasota", 237),
    "gainesville": ("gainesville", 23),
    "tallahassee": ("tallahassee", 53),
    "naples": ("naples", 264),
    "new york": ("newyork", 1),
    "los angeles": ("losangeles", 3),
    "chicago": ("chicago", 7),
    "houston": ("houston", 25),
    "dallas": ("dallas", 14),
    "atlanta": ("atlanta", 5),
    "phoenix": ("phoenix", 43),
    "philadelphia": ("philadelphia", 42),
    "san antonio": ("sanantonio", 46),
    "san diego": ("sandiego", 47),
    "denver": ("denver", 15),
    "seattle": ("seattle", 50),
    "boston": ("boston", 6),
    "nashville": ("nashville", 40),
    "charlotte": ("charlotte", 8),
    "austin": ("austin", 4),
}

# Cache of dynamically discovered area IDs
_area_id_cache: dict[str, int] = {}


def _city_to_map(location: str) -> tuple[str, int]:
    """Returns (subdomain, area_id) for a location string."""
    if not location:
        return ("tampa", 37)
    city = location.split(",")[0].strip().lower()
    if city in CITY_MAP:
        return CITY_MAP[city]
    # Fallback subdomain from city name
    subdomain = city.replace(" ", "")
    area_id = _area_id_cache.get(subdomain, 0)
    return (subdomain, area_id)


def _parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    nums = re.sub(r"[^\d]", "", str(text))
    return float(nums) if nums else None


def _parse_mileage_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"([\d,]+)\s*(?:mi|miles)", text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r"(\d+)k\s*(?:mi|miles)?", text, re.IGNORECASE)
    if match:
        return int(match.group(1)) * 1000
    return None


def _parse_year_from_title(title: str) -> Optional[int]:
    match = re.search(r'\b(19|20)\d{2}\b', title or "")
    return int(match.group()) if match else None


def _is_dealer(title: str, description: str = "") -> bool:
    dealer_signals = ["dealer", "dealership", "financing", "warranty", "certified", "we finance"]
    text = f"{title} {description}".lower()
    return any(s in text for s in dealer_signals)


def _decode_photo_url(code: str) -> str:
    """Convert sapi photo code '3:00L0L_imageId_postCode' to full image URL."""
    # Strip the leading "3:" prefix
    if code.startswith("3:"):
        code = code[2:]
    return f"https://images.craigslist.org/{code}_600x450.jpg"


def _decode_item(item: list, decode: dict, subdomain: str, search_category: str) -> Optional[dict]:
    """Parse a sapi encoded item array into a dict with listing fields."""
    try:
        title = item[-1] if isinstance(item[-1], str) else None
        if not title:
            return None

        # item[3] is always the raw price integer
        price = float(item[3]) if item[3] else None

        # Extract typed sub-arrays
        mileage = None
        slug = None
        photos = []
        for el in item:
            if not isinstance(el, list) or len(el) < 2:
                continue
            tag = el[0]
            if tag == 9:  # mileage integer
                mileage = int(el[1]) if el[1] else None
            elif tag == 6:  # url slug
                slug = el[1]
            elif tag == 4:  # photo array ["3:code", ...]
                photos = [_decode_photo_url(p) for p in el[1:] if isinstance(p, str)]

        if not price:
            return None

        # Location index is first number in item[4] e.g. "1:2~27.9~-82.3"
        loc_idx_str = str(item[4]).split(":")[0] if item[4] else "0"
        try:
            loc_idx = int(loc_idx_str)
        except ValueError:
            loc_idx = 0

        locations = decode.get("locations", [])
        loc_entry = locations[loc_idx] if loc_idx < len(locations) else None

        site = subdomain
        subarea = None
        if loc_entry and isinstance(loc_entry, list):
            if len(loc_entry) >= 2:
                site = loc_entry[1]
            if len(loc_entry) >= 3:
                subarea = loc_entry[2]

        # Posting ID = minPostingId + item[0]
        min_id = decode.get("minPostingId", 0)
        posting_id = min_id + item[0]

        if subarea:
            url = f"https://{site}.craigslist.org/{subarea}/{search_category}/d/{slug}/{posting_id}.html"
        else:
            url = f"https://{site}.craigslist.org/{search_category}/d/{slug}/{posting_id}.html"

        # Location description from decode
        loc_descs = decode.get("locationDescriptions", [])
        loc_desc_idx = int(str(item[4]).split(":")[1].split("~")[0]) if ":" in str(item[4]) else 0
        location_name = loc_descs[loc_desc_idx] if loc_desc_idx < len(loc_descs) else site.title()

        year = _parse_year_from_title(title)
        external_id = str(posting_id)

        return {
            "title": title,
            "url": url,
            "external_id": external_id,
            "price": price,
            "mileage": mileage,
            "year": year,
            "location": location_name,
            "image_url": photos[0] if photos else None,
            "photos": photos,
        }
    except Exception as e:
        logger.debug(f"Failed to decode CL sapi item: {e}")
        return None


async def _fetch_area_id(subdomain: str, client: httpx.AsyncClient) -> int:
    """Dynamically discover area ID from Craigslist city page HTML."""
    if subdomain in _area_id_cache:
        return _area_id_cache[subdomain]
    try:
        resp = await client.get(f"https://{subdomain}.craigslist.org/search/cto", timeout=10)
        matches = re.findall(r'areaId["\s:]+(\d+)', resp.text)
        if matches:
            area_id = int(matches[0])
            _area_id_cache[subdomain] = area_id
            logger.info(f"Discovered areaId={area_id} for {subdomain}")
            return area_id
    except Exception as e:
        logger.warning(f"Failed to discover areaId for {subdomain}: {e}")
    return 0


class CraigslistAdapter(SourceAdapter):
    source_name = "craigslist"

    async def search(self, params: SearchParams) -> list[NormalizedListing]:
        subdomain, area_id = _city_to_map(params.location)

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            # Dynamically discover area ID if unknown
            if not area_id:
                area_id = await _fetch_area_id(subdomain, client)
            if not area_id:
                logger.warning(f"No area ID for {subdomain}, skipping Craigslist search")
                return []

            sapi_params = {
                "batch": f"{area_id}-0-360-0-0",
                "cc": "US",
                "lang": "en",
                "query": params.query or "",
                "searchPath": "cto",
                "purveyor": "owner",
                "auto_title_status": 1,
            }
            if params.max_price:
                sapi_params["max_price"] = int(params.max_price)
            if params.min_price:
                sapi_params["min_price"] = int(params.min_price)
            if params.max_mileage:
                sapi_params["max_auto_miles"] = int(params.max_mileage)
            if params.min_year:
                sapi_params["min_auto_year"] = int(params.min_year)

            logger.info(f"Craigslist sapi search: {subdomain} (areaId={area_id}) — {params.query}")

            try:
                resp = await client.get(
                    "https://sapi.craigslist.org/web/v8/postings/search/full",
                    params=sapi_params,
                    headers=SAPI_HEADERS,
                )
                if resp.status_code != 200:
                    logger.warning(f"Craigslist sapi returned {resp.status_code}")
                    return []
                data = resp.json().get("data", {})
            except Exception as e:
                logger.error(f"Craigslist sapi fetch failed: {e}")
                return []

        return self._parse_sapi_results(data, subdomain, params)

    def _parse_sapi_results(self, data: dict, subdomain: str, params: SearchParams) -> list[NormalizedListing]:
        items = data.get("items", [])
        decode = data.get("decode", {})
        listings = []
        seen = set()

        for raw_item in items:
            try:
                item = _decode_item(raw_item, decode, subdomain, "cto")
                if not item:
                    continue

                title = item["title"]
                if _is_dealer(title):
                    continue

                ext_id = item["external_id"]
                if ext_id in seen:
                    continue
                seen.add(ext_id)

                # Post-filter (sapi filters server-side but double-check)
                if params.max_price and item["price"] and item["price"] > params.max_price:
                    continue
                if params.max_mileage and item["mileage"] and item["mileage"] > params.max_mileage:
                    continue

                listings.append(NormalizedListing(
                    source="craigslist",
                    external_id=ext_id,
                    url=item["url"],
                    title=title,
                    year=item["year"],
                    price=item["price"],
                    mileage=item["mileage"],
                    location=item["location"],
                    image_url=item["image_url"],
                    seller_type="private",
                    raw_data={"photos": item["photos"]},
                ))
            except Exception as e:
                logger.debug(f"Failed to parse CL item: {e}")
                continue

        logger.info(f"Craigslist returned {len(listings)} listings from {subdomain}")
        return listings[:30]

    async def fetch_detail(self, url: str) -> Optional[NormalizedListing]:
        """Fetch a single Craigslist listing for full description, attributes, and photos."""
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                return self._parse_detail(resp.text, url)
        except Exception as e:
            logger.error(f"CL detail fetch failed: {e}")
            return None

    def _parse_detail(self, html: str, url: str) -> Optional[NormalizedListing]:
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("#titletextonly") or soup.select_one("h1.postingtitle")
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = soup.select_one(".price")
        price = _parse_price(price_el.get_text() if price_el else "")

        desc_el = soup.select_one("#postingbody")
        description = desc_el.get_text("\n", strip=True) if desc_el else ""
        description = re.sub(r"QR Code Link to This Post\n?", "", description).strip()

        # Parse attributes — each is a div.attr with span.labl and span.valu
        attrs = {}
        for attr_div in soup.select(".attrgroup .attr"):
            labl = attr_div.select_one(".labl")
            valu = attr_div.select_one(".valu")
            if labl and valu:
                key = labl.get_text(strip=True).rstrip(":").strip().lower()
                val = valu.get_text(strip=True)
                if key and val:
                    attrs[key] = val

        # Year and make/model from first attrgroup header
        year_span = soup.select_one(".valu.year")
        makemodel_span = soup.select_one(".valu.makemodel")

        year_val = year_span.get_text(strip=True) if year_span else None
        raw_makemodel = makemodel_span.get_text(strip=True) if makemodel_span else ""
        # "honda civic" → make=honda, model=civic
        mm_parts = raw_makemodel.split(None, 1)
        make_val = mm_parts[0].title() if mm_parts else None
        model_val = mm_parts[1].title() if len(mm_parts) > 1 else None

        mileage_str = attrs.get("odometer")
        vin_val = attrs.get("vin")

        mileage = int(re.sub(r"[^\d]", "", str(mileage_str))) if mileage_str else _parse_mileage_from_text(description)
        year = int(year_val) if year_val and str(year_val).isdigit() else _parse_year_from_title(title)

        photos = []
        for img in soup.select(".gallery img, #thumbs img"):
            src = img.get("src", "")
            if src:
                full = re.sub(r"_\d+x\d+\.", "_1200x900.", src)
                photos.append(full)

        external_id = None
        id_match = re.search(r"/(\d{10,})", url)
        if id_match:
            external_id = id_match.group(1)

        subdomain_match = re.search(r"https://([^.]+)\.craigslist", url)
        subdomain = subdomain_match.group(1) if subdomain_match else "unknown"

        vehicle_specs = {k: v for k, v in {
            "condition": attrs.get("condition"),
            "body_type": attrs.get("type"),
            "cylinders": attrs.get("cylinders"),
            "transmission": attrs.get("transmission"),
            "drive": attrs.get("drive"),
            "fuel": attrs.get("fuel"),
            "paint_color": attrs.get("paint color"),
            "title_status": attrs.get("title status"),
        }.items() if v}

        return NormalizedListing(
            source="craigslist",
            external_id=external_id,
            url=url,
            title=title,
            year=year,
            make=make_val,
            model=model_val,
            price=price or 0,
            mileage=mileage,
            location=subdomain.replace("-", " ").title(),
            description=description,
            image_url=photos[0] if photos else None,
            vin=vin_val,
            seller_type="private",
            raw_data={"photos": photos, "attrs": attrs, "vehicle_specs": vehicle_specs},
        )
