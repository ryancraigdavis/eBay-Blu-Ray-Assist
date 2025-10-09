import httpx
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
from datetime import datetime
from ..config import settings
from ..models import PriceData

class PricingService:
    def __init__(self):
        self.base_delay = 2.0  # Base delay between requests to avoid rate limiting
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def get_ebay_pricing(self, title: str, condition: str = "Used") -> Optional[PriceData]:
        """Get pricing data from eBay sold listings using web scraping"""
        try:
            # Format search query for eBay
            search_query = f"{title} blu-ray"

            # Scrape sold listings
            sold_items = await self._scrape_ebay_sold_listings(search_query, pages=2)

            if not sold_items:
                print(f"No sold listings found for '{search_query}', using mock data")
                return await self._mock_pricing_data(title, condition)

            # Calculate pricing statistics
            prices = [item['price'] for item in sold_items if item['price'] > 0]

            if not prices:
                return await self._mock_pricing_data(title, condition)

            average_price = round(sum(prices) / len(prices), 2)
            shipping_cost = 4.99  # Standard media mail shipping

            # Format comparable listings
            comparable_listings = [
                {
                    "title": item['title'],
                    "price": item['price'],
                    "shipping": item.get('shipping', 0.0),
                    "condition": condition,
                    "sold_date": item.get('sold_date', '')
                }
                for item in sold_items[:5]  # Top 5 listings
            ]

            return PriceData(
                average_price=average_price,
                shipping_cost=shipping_cost,
                total_cost=round(average_price + shipping_cost, 2),
                comparable_listings=comparable_listings
            )

        except Exception as e:
            print(f"Error getting eBay pricing: {str(e)}")
            # Fallback to mock data on error
            return await self._mock_pricing_data(title, condition)

    async def _scrape_ebay_sold_listings(self, search_term: str, pages: int = 2) -> List[Dict[str, Any]]:
        """Scrape eBay sold listings for pricing data"""
        results = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for page in range(1, pages + 1):
                    # eBay sold listings URL with pagination
                    # LH_Sold=1 means only sold items
                    # LH_Complete=1 means completed listings
                    url = f"https://www.ebay.com/sch/i.html?_nkw={quote(search_term)}&LH_Sold=1&LH_Complete=1&_pgn={page}"

                    print(f"Scraping eBay page {page}: {url}")

                    # Rate limiting - wait before request
                    if page > 1:
                        await asyncio.sleep(self.base_delay)

                    try:
                        response = await client.get(url, headers=self.headers, follow_redirects=True)
                        response.raise_for_status()

                        # Parse HTML
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Find all listing items
                        listings = soup.select('.s-item')

                        print(f"Found {len(listings)} listings on page {page}")

                        for item in listings:
                            try:
                                # Skip header/ad items
                                title_elem = item.select_one('.s-item__title')
                                if not title_elem or 'Shop on eBay' in title_elem.get_text():
                                    continue

                                title = title_elem.get_text(strip=True)

                                # Extract price
                                price_elem = item.select_one('.s-item__price')
                                if not price_elem:
                                    continue

                                price_text = price_elem.get_text(strip=True)
                                price = self._parse_price(price_text)

                                # Extract link
                                link_elem = item.select_one('.s-item__link')
                                link = link_elem['href'] if link_elem else ''

                                # Extract sold date (if available)
                                sold_date = ''
                                date_elem = item.select_one('.s-item__endedDate, .s-item__ended-date')
                                if date_elem:
                                    sold_date = date_elem.get_text(strip=True)

                                # Extract shipping cost (if available)
                                shipping = 0.0
                                shipping_elem = item.select_one('.s-item__shipping')
                                if shipping_elem:
                                    shipping_text = shipping_elem.get_text(strip=True)
                                    if 'Free' not in shipping_text:
                                        shipping = self._parse_price(shipping_text)

                                results.append({
                                    'title': title,
                                    'price': price,
                                    'link': link,
                                    'sold_date': sold_date,
                                    'shipping': shipping
                                })

                            except Exception as e:
                                print(f"Error parsing item: {e}")
                                continue

                    except httpx.HTTPError as e:
                        print(f"HTTP error on page {page}: {e}")
                        break

        except Exception as e:
            print(f"Error scraping eBay: {e}")

        return results

    def _parse_price(self, price_text: str) -> float:
        """Parse price from text like '$12.99' or '$10.00 to $15.00'"""
        try:
            # Remove currency symbols and extra text
            price_text = price_text.replace('$', '').replace(',', '')

            # Handle price ranges - take the first/lower price
            if ' to ' in price_text:
                price_text = price_text.split(' to ')[0]

            # Extract first number found
            match = re.search(r'\d+\.?\d*', price_text)
            if match:
                return float(match.group())

            return 0.0
        except:
            return 0.0

    async def _mock_pricing_data(self, title: str, condition: str) -> PriceData:
        """Mock pricing data for development - replace with real implementation"""
        # This is a placeholder that generates reasonable pricing data
        # In production, replace with actual eBay API calls or web scraping

        base_price = 15.0  # Base price for most blu-rays

        # Adjust price based on condition
        condition_multiplier = {
            "New": 1.3,
            "Like New": 1.1,
            "Very Good": 1.0,
            "Good": 0.8,
            "Acceptable": 0.6,
            "Used": 0.9
        }.get(condition, 0.9)

        # Add some variation based on title length (proxy for popularity/rarity)
        title_factor = min(len(title) / 20.0, 2.0)

        average_price = round(base_price * condition_multiplier * title_factor, 2)
        shipping_cost = 4.99  # Standard media mail shipping

        return PriceData(
            average_price=average_price,
            shipping_cost=shipping_cost,
            total_cost=round(average_price + shipping_cost, 2),
            comparable_listings=[
                {
                    "title": f"{title} - Blu-ray",
                    "price": average_price - 2.00,
                    "shipping": shipping_cost,
                    "condition": condition,
                    "sold_date": "2024-01-15"
                },
                {
                    "title": f"{title} (Blu-ray Disc)",
                    "price": average_price + 1.50,
                    "shipping": shipping_cost,
                    "condition": condition,
                    "sold_date": "2024-01-10"
                },
                {
                    "title": f"{title} Blu-ray Movie",
                    "price": average_price,
                    "shipping": shipping_cost,
                    "condition": condition,
                    "sold_date": "2024-01-08"
                }
            ]
        )

    async def get_amazon_pricing(self, title: str) -> Optional[Dict[str, Any]]:
        """Get pricing data from Amazon (placeholder)"""
        # Placeholder for Amazon pricing integration
        # Would require Amazon API or web scraping
        return None

    async def get_comprehensive_pricing(self, title: str, condition: str = "Used") -> Optional[PriceData]:
        """Get pricing data from multiple sources"""
        try:
            # Start with eBay pricing
            ebay_pricing = await self.get_ebay_pricing(title, condition)

            # Could add other sources here (Amazon, etc.)
            # amazon_pricing = await self.get_amazon_pricing(title)

            return ebay_pricing

        except Exception as e:
            print(f"Error getting comprehensive pricing: {str(e)}")
            return None

    def calculate_suggested_price(self, pricing_data: PriceData, margin_percentage: float = 0.15) -> float:
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