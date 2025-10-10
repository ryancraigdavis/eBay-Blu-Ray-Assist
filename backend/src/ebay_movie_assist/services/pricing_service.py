import httpx
import asyncio
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ..config import settings
from ..models import PriceData


class PricingService:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """Get OAuth access token using client credentials grant flow"""
        # Check if we have a valid cached token
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        # Validate credentials
        app_id = settings.EBAY_APP_ID or settings.EBAY_API_KEY
        cert_id = settings.EBAY_CERT_ID

        if not app_id or not cert_id:
            raise ValueError(
                "eBay API credentials not configured. "
                "Set EBAY_APP_ID and EBAY_CERT_ID in Doppler."
            )

        # Create Basic Auth header
        credentials = f"{app_id}:{cert_id}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64_credentials}",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.EBAY_OAUTH_URL, headers=headers, data=data
                )
                response.raise_for_status()
                token_data = response.json()

                self.access_token = token_data["access_token"]
                # Token expires in 7200 seconds (2 hours), refresh 5 min before expiry
                expires_in = token_data.get("expires_in", 7200)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

                return self.access_token

        except httpx.HTTPError as e:
            print(f"Error getting eBay OAuth token: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            raise ValueError(f"Failed to get eBay access token: {str(e)}")

    async def _search_ebay_listings(
        self, search_query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for active eBay listings using Browse API"""
        try:
            access_token = await self._get_access_token()

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",  # US marketplace
            }

            # Build search query
            # Filter for Blu-ray category (11232) and condition
            params = {
                "q": search_query,
                "category_ids": "11232",  # DVDs & Movies category
                "limit": str(limit),
                "sort": "price",  # Sort by price ascending to get lowest first
                "filter": "buyingOptions:{FIXED_PRICE}",  # Only Buy It Now listings
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{settings.EBAY_BROWSE_API_URL}/item_summary/search",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                items = data.get("itemSummaries", [])

                for item in items:
                    # Extract price information
                    price_info = item.get("price", {})
                    price = 0.0
                    if price_info:
                        price_value = price_info.get("value")
                        if price_value:
                            price = float(price_value)

                    # Extract shipping cost
                    shipping = 0.0
                    shipping_options = item.get("shippingOptions", [])
                    if shipping_options:
                        shipping_cost = shipping_options[0].get("shippingCost", {})
                        if shipping_cost:
                            shipping_value = shipping_cost.get("value")
                            if shipping_value:
                                shipping = float(shipping_value)

                    results.append(
                        {
                            "title": item.get("title", ""),
                            "price": price,
                            "shipping": shipping,
                            "condition": item.get("condition", ""),
                            "itemId": item.get("itemId", ""),
                            "itemWebUrl": item.get("itemWebUrl", ""),
                        }
                    )

                return results

        except httpx.HTTPError as e:
            print(f"Error searching eBay listings: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error searching eBay: {e}")
            raise

    async def get_ebay_pricing(
        self, title: str, condition: str = "Used"
    ) -> Optional[PriceData]:
        """Get pricing data from eBay active listings using Browse API"""
        try:
            # Format search query for eBay
            search_query = f"{title} blu-ray"

            # Search for listings
            listings = await self._search_ebay_listings(search_query, limit=10)

            if not listings:
                print(f"No active listings found for '{search_query}'")
                return None

            # Filter out listings with no price
            valid_listings = [item for item in listings if item["price"] > 0]

            if not valid_listings:
                print(f"No listings with valid prices found for '{search_query}'")
                return None

            # Sort by total cost (price + shipping)
            valid_listings.sort(key=lambda x: x["price"] + x.get("shipping", 0))

            # Take the lowest 5-10 listings
            num_listings = min(10, len(valid_listings))
            lowest_listings = valid_listings[:num_listings]

            # Calculate average price from lowest listings
            prices = [item["price"] for item in lowest_listings]
            average_price = round(sum(prices) / len(prices), 2)

            # Standard shipping cost (can be overridden)
            shipping_cost = 4.99

            # Format comparable listings
            comparable_listings = [
                {
                    "title": item["title"],
                    "price": item["price"],
                    "shipping": item.get("shipping", 0.0),
                    "condition": item.get("condition", condition),
                    "itemId": item.get("itemId", ""),
                    "url": item.get("itemWebUrl", ""),
                }
                for item in lowest_listings[:5]  # Top 5 lowest listings
            ]

            return PriceData(
                average_price=average_price,
                shipping_cost=shipping_cost,
                total_cost=round(average_price + shipping_cost, 2),
                comparable_listings=comparable_listings,
            )

        except Exception as e:
            print(f"Error getting eBay pricing: {str(e)}")
            return None

    async def _get_mock_pricing(self, title: str, condition: str = "Used") -> PriceData:
        """Return mock pricing data for development"""
        average_price = 8.50
        shipping_cost = 4.99

        # Generate some mock comparable listings
        comparable_listings = [
            {
                "title": f"{title} (Blu-ray Disc)",
                "price": 7.99,
                "shipping": 4.99,
                "condition": condition,
                "itemId": "mock-item-1",
                "url": "",
            },
            {
                "title": f"{title} Blu-ray",
                "price": 8.50,
                "shipping": 0.0,
                "condition": condition,
                "itemId": "mock-item-2",
                "url": "",
            },
            {
                "title": f"{title} - Blu-ray Movie",
                "price": 8.99,
                "shipping": 4.99,
                "condition": condition,
                "itemId": "mock-item-3",
                "url": "",
            },
            {
                "title": f"{title} (Blu-ray)",
                "price": 9.25,
                "shipping": 3.99,
                "condition": condition,
                "itemId": "mock-item-4",
                "url": "",
            },
            {
                "title": f"{title} Blu-ray Disc",
                "price": 7.50,
                "shipping": 5.99,
                "condition": condition,
                "itemId": "mock-item-5",
                "url": "",
            },
        ]

        return PriceData(
            average_price=average_price,
            shipping_cost=shipping_cost,
            total_cost=round(average_price + shipping_cost, 2),
            comparable_listings=comparable_listings,
        )

    async def get_comprehensive_pricing(
        self, title: str, condition: str = "Used"
    ) -> Optional[PriceData]:
        """Get pricing data from eBay Browse API (with fallback to mock data)"""
        try:
            # Check if eBay credentials are configured
            app_id = settings.EBAY_APP_ID or settings.EBAY_API_KEY
            cert_id = settings.EBAY_CERT_ID

            # If credentials not configured, use mock data
            if not app_id or not cert_id:
                print(f"eBay API credentials not configured, using mock pricing data")
                return await self._get_mock_pricing(title, condition)

            # Try to get real eBay pricing
            ebay_pricing = await self.get_ebay_pricing(title, condition)

            if not ebay_pricing:
                print(f"No pricing data available for '{title}', using mock data")
                return await self._get_mock_pricing(title, condition)

            return ebay_pricing

        except Exception as e:
            print(f"Error getting comprehensive pricing: {str(e)}, using mock data")
            return await self._get_mock_pricing(title, condition)

    def calculate_suggested_price(
        self, pricing_data: PriceData, margin_percentage: float = 0.15
    ) -> float:
        """Calculate suggested selling price based on market data"""
        if not pricing_data or not pricing_data.average_price:
            return 12.99  # Default fallback price

        # Add margin to average price
        suggested_price = pricing_data.average_price * (1 + margin_percentage)

        # Round to nearest .99 or .49
        if suggested_price < 10:
            return round(suggested_price - 0.01, 2)  # x.99
        else:
            return round(suggested_price - 0.51, 2) + 0.49  # x.49


pricing_service = PricingService()
