import os
import re
import json
from urllib.parse import quote
from typing import Optional

from app.adapters.base import SourceAdapter, NormalizedListing, SearchParams
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from scrapfly import ScrapflyClient, ScrapeConfig
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False
    logger.warning("scrapfly-sdk not installed — Facebook adapter disabled")

BASE_CONFIG = {
    "asp": True,
    "country": "US",
    "render_js": True,
    "rendering_wait": 5000,
    "proxy_pool": "public_residential_pool",
}


def _find_nodes(data, typenames: set, depth: int = 0, max_depth: int = 50) -> list:
    """Recursively walk parsed JSON and collect nodes matching target __typename values."""
    if depth > max_depth:
        return []
    results = []
    if isinstance(data, dict):
        if data.get("__typename") in typenames:
            results.append(data)
        for value in data.values():
            results.extend(_find_nodes(value, typenames, depth + 1, max_depth))
    elif isinstance(data, list):
        for item in data:
            results.extend(_find_nodes(item, typenames, depth + 1, max_depth))
    return results


def _parse_price(node: dict) -> Optional[float]:
    try:
        price_info = node.get("listing_price") or node.get("price") or {}
        amount = price_info.get("amount") or price_info.get("amount_with_offset_in_currency") or "0"
        return float(re.sub(r"[^\d.]", "", str(amount)))
    except Exception:
        return None


def _parse_location(node: dict) -> Optional[str]:
    try:
        loc = node.get("location") or {}
        reverse = loc.get("reverse_geocode") or {}
        city_page = reverse.get("city_page") or {}
        display = city_page.get("display_name")
        if display:
            return display
        city = reverse.get("city") or ""
        state = reverse.get("state") or ""
        if city or state:
            return f"{city}, {state}".strip(", ")
        return None
    except Exception:
        return None


def _parse_mileage(node: dict) -> Optional[int]:
    """Extract mileage from vehicle_info or subtitle strings like '100K miles'."""
    # Try vehicle_info first
    vehicle = node.get("vehicle_info") or {}
    mileage_str = vehicle.get("odometer_reading", "")
    if mileage_str:
        return int(re.sub(r"[^\d]", "", str(mileage_str)))

    # Fall back to subtitle — FB puts "100K miles" or "176,000 miles" here
    subtitles = node.get("custom_sub_titles_with_rendering_flags") or []
    for sub in subtitles:
        text = (sub.get("subtitle") or "").lower()
        if "mile" in text or "mi" in text:
            # Handle "100K miles" → 100000, "176,000 miles" → 176000
            text_clean = text.replace(",", "").replace("k miles", "000").replace("k mi", "000")
            nums = re.findall(r"\d+", text_clean)
            if nums:
                return int(nums[0])
    return None


def _normalize_node(node: dict) -> Optional[NormalizedListing]:
    """Map a raw Facebook marketplace JSON node to our NormalizedListing schema."""
    try:
        # Prefer custom_title (no middot characters), fall back to raw title
        title = (
            node.get("custom_title")
            or node.get("marketplace_listing_title")
            or node.get("name")
            or ""
        )
        price = _parse_price(node)
        if not title or price is None:
            return None

        listing_id = node.get("id", "")
        url = f"https://www.facebook.com/marketplace/item/{listing_id}/" if listing_id else None

        primary_photo = node.get("primary_listing_photo") or {}
        image = (primary_photo.get("image") or {}).get("uri")

        description = (node.get("redacted_description") or {}).get("text")

        seller = node.get("marketplace_listing_seller") or node.get("seller") or {}
        seller_name = seller.get("name")

        mileage = _parse_mileage(node)

        return NormalizedListing(
            source="facebook",
            external_id=listing_id or None,
            url=url,
            title=title,
            price=price,
            mileage=mileage,
            location=_parse_location(node),
            description=description,
            image_url=image,
            seller_name=seller_name,
            seller_type="private",
            is_sold=node.get("is_sold", False),
            is_pending=node.get("is_pending", False),
            raw_data=node,
        )
    except Exception as e:
        logger.debug(f"Failed to normalize FB node: {e}")
        return None


def _parse_response_html(html: str) -> list[NormalizedListing]:
    """Extract all marketplace listing nodes from the raw HTML response."""
    listings = []
    seen_ids = set()

    # FB embeds data in multiple <script type="application/json"> blocks
    script_blocks = re.findall(
        r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )

    target_typenames = {"GroupCommerceProductItem", "MarketplaceProductItem"}

    for block in script_blocks:
        try:
            data = json.loads(block)
            nodes = _find_nodes(data, target_typenames)
            for node in nodes:
                listing = _normalize_node(node)
                if listing and listing.external_id not in seen_ids:
                    seen_ids.add(listing.external_id)
                    listings.append(listing)
        except Exception:
            continue

    return listings


class FacebookScrapflyAdapter(SourceAdapter):
    source_name = "facebook"

    def __init__(self):
        self._client = None
        if _SDK_AVAILABLE and settings.SCRAPFLY_KEY:
            self._client = ScrapflyClient(key=settings.SCRAPFLY_KEY)

    def _ready(self) -> bool:
        return self._client is not None

    def _location_slug(self, location: str) -> str:
        """Convert 'Tampa, FL' → 'tampa' for Facebook's city marketplace URLs."""
        if not location:
            return "marketplace"
        # Take only the city part (before the comma), lowercase, spaces to hyphens
        city = location.split(",")[0].strip().lower().replace(" ", "-")
        return city

    async def search(self, params: SearchParams) -> list[NormalizedListing]:
        if not self._ready():
            logger.warning("Scrapfly SDK not ready (missing key or package). Skipping Facebook search.")
            return []

        # Use city-path URL — this actually filters by location unlike query params
        city_slug = self._location_slug(params.location)
        query_enc = quote(params.query or "")
        url = f"https://www.facebook.com/marketplace/{city_slug}/search/?query={query_enc}"

        if params.max_price:
            url += f"&maxPrice={int(params.max_price)}"
        if params.min_price:
            url += f"&minPrice={int(params.min_price)}"

        logger.info(f"Facebook search: {url}")

        try:
            result = await self._client.async_scrape(ScrapeConfig(url=url, **BASE_CONFIG))
            listings = _parse_response_html(result.content)
            logger.info(f"Facebook returned {len(listings)} raw listings")
        except Exception as e:
            logger.error(f"Facebook search failed: {e}")
            return []

        # Client-side filter by mileage (FB URL params don't always filter reliably)
        filtered = []
        for l in listings:
            if params.max_mileage and l.mileage and l.mileage > params.max_mileage:
                continue
            filtered.append(l)

        return filtered[:25]

    async def fetch_detail(self, url: str) -> Optional[NormalizedListing]:
        """
        Fetch a single listing detail page — returns full vehicle data including
        description, exact mileage, make/model/trim, colors, transmission,
        title status, VIN, and all photos.
        """
        if not self._ready():
            return None

        try:
            result = await self._client.async_scrape(ScrapeConfig(url=url, **BASE_CONFIG))
            return _parse_detail_page(result.content, url)
        except Exception as e:
            logger.error(f"Facebook detail fetch failed: {e}")
        return None


def _find_by_typename(data, typename, depth=0, max_depth=60):
    if depth > max_depth:
        return []
    results = []
    if isinstance(data, dict):
        if data.get("__typename") == typename:
            results.append(data)
        for v in data.values():
            results.extend(_find_by_typename(v, typename, depth + 1))
    elif isinstance(data, list):
        for item in data:
            results.extend(_find_by_typename(item, typename, depth + 1))
    return results


def _parse_detail_page(html: str, url: str) -> Optional[NormalizedListing]:
    """
    Parse a Facebook listing detail page — extracts the richest available data:
    description, exact mileage, make/model/trim, colors, transmission,
    title status, VIN, GPS coords, and all photos.
    """
    script_pattern = re.compile(
        r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
        re.DOTALL,
    )
    blocks = script_pattern.findall(html)

    # Find the largest GroupCommerceProductItem — detail page has full vehicle data
    best_node = None
    best_size = 0
    all_photos = []

    for block in blocks:
        try:
            data = json.loads(block)

            # Get all photos from MarketplaceVehicleProductDetailsPage
            detail_pages = _find_by_typename(data, "MarketplaceVehicleProductDetailsPage")
            for dp in detail_pages:
                target = dp.get("target") or {}
                photos = target.get("listing_photos") or []
                for photo in photos:
                    uri = (photo.get("image") or {}).get("uri")
                    if uri:
                        all_photos.append(uri)

            # Get the most complete listing node
            nodes = _find_by_typename(data, "GroupCommerceProductItem")
            for node in nodes:
                size = len(json.dumps(node))
                if size > best_size:
                    best_size = size
                    best_node = node
        except Exception:
            continue

    if not best_node:
        return None

    # Build normalized listing from full detail node
    title = best_node.get("custom_title") or best_node.get("marketplace_listing_title") or ""
    price = _parse_price(best_node)
    if not title or price is None:
        return None

    listing_id = best_node.get("id", "")

    # Exact mileage from structured vehicle data
    odometer = best_node.get("vehicle_odometer_data") or {}
    mileage = odometer.get("value") or _parse_mileage(best_node)

    # Make / model / trim from structured fields
    make  = best_node.get("vehicle_make_display_name")
    model = best_node.get("vehicle_model_display_name")
    trim  = best_node.get("vehicle_trim_display_name")

    # Title status
    raw_title_status = (best_node.get("vehicle_title_status") or "").lower()
    title_status = "clean"
    if "salvage" in raw_title_status:
        title_status = "salvage"
    elif "rebuilt" in raw_title_status or "reconstructed" in raw_title_status:
        title_status = "rebuilt"

    # VIN
    vin = best_node.get("vehicle_identification_number")

    # Description
    description = (best_node.get("redacted_description") or {}).get("text")

    # Enrich description with vehicle specs for scoring engine
    specs = []
    transmission = best_node.get("vehicle_transmission_type", "")
    fuel_type     = best_node.get("vehicle_fuel_type", "")
    ext_color     = best_node.get("vehicle_exterior_color", "")
    int_color     = best_node.get("vehicle_interior_color", "")
    seller_type   = best_node.get("vehicle_seller_type", "")

    if transmission:
        specs.append(f"Transmission: {transmission}")
    if fuel_type:
        specs.append(f"Fuel: {fuel_type}")
    if ext_color:
        specs.append(f"Exterior: {ext_color}")
    if int_color:
        specs.append(f"Interior: {int_color}")
    if seller_type:
        specs.append(f"Seller: {seller_type.replace('_', ' ').title()}")

    if specs and description:
        description = description + "\n\n" + " | ".join(specs)
    elif specs:
        description = " | ".join(specs)

    # Location
    location = _parse_location(best_node)

    # Primary image — prefer full-size detail photos over thumbnail
    image_url = all_photos[0] if all_photos else None
    if not image_url:
        primary_photo = best_node.get("primary_listing_photo") or {}
        image_url = (primary_photo.get("image") or {}).get("uri")

    # Store extra photos + specs in raw_data for the frontend gallery
    raw_data = {
        **best_node,
        "_all_photos": all_photos,
        "_transmission": transmission,
        "_fuel_type": fuel_type,
        "_exterior_color": ext_color,
        "_interior_color": int_color,
        "_seller_type": seller_type,
    }

    return NormalizedListing(
        source="facebook",
        external_id=listing_id or None,
        url=url,
        title=title,
        year=_parse_year_from_title(title),
        make=make,
        model=model,
        trim=trim,
        price=price,
        mileage=mileage,
        location=location,
        description=description,
        image_url=image_url,
        vin=vin,
        seller_type=seller_type.replace("_SELLER", "").lower() if seller_type else "private",
        is_sold=best_node.get("is_sold", False),
        is_pending=best_node.get("is_pending", False),
        raw_data=raw_data,
    )


def _parse_year_from_title(title: str) -> Optional[int]:
    if not title:
        return None
    match = re.search(r'\b(19|20)\d{2}\b', title)
    return int(match.group()) if match else None
