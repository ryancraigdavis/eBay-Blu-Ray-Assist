import pandas as pd
import os
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models import BlurayItem, MovieMetadata, PriceData

class TemplateService:
    def __init__(self):
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "template"
        )
        # Find the first eBay template CSV file in the directory
        template_files = glob.glob(os.path.join(template_dir, "eBay-category-listing-template-*.csv"))
        if not template_files:
            raise ValueError(f"No eBay template CSV found in {template_dir}")
        # Use the most recently modified template file
        self.template_path = max(template_files, key=os.path.getmtime)

        # Load and cache the template columns
        self._template_columns = None
        self._load_template_columns()

    def _load_template_columns(self):
        """Load template columns from the eBay CSV file"""
        try:
            # Read just the header row - eBay template has headers in first row
            # The file uses UTF-8 with BOM
            df = pd.read_csv(self.template_path, nrows=0, encoding='utf-8-sig')
            self._template_columns = list(df.columns)
        except Exception as e:
            raise ValueError(f"Failed to load template columns: {str(e)}")

    def load_template(self) -> pd.DataFrame:
        """Load the eBay template CSV header"""
        try:
            return pd.read_csv(self.template_path, nrows=0, encoding='utf-8-sig')
        except Exception as e:
            raise ValueError(f"Failed to load template: {str(e)}")

    def _get_action_column(self) -> str:
        """Get the Action column name from the template (column 3 contains *Action in its name)"""
        if self._template_columns and len(self._template_columns) > 2:
            # Column 3 (index 2) contains the Action field in eBay's format
            # It's named something like "Template=fx_category_template_EBAY_US*Action(...)"
            return self._template_columns[2]
        return '*Action'

    def create_listing_row(self, item: BlurayItem) -> Dict[str, Any]:
        """Create a single row of eBay listing data from a BlurayItem"""
        row = {}

        # Get the custom price if provided in custom_fields, otherwise calculate
        custom_price = None
        custom_quantity = '1'
        custom_description = None
        custom_location = 'United States'

        if item.custom_fields:
            if 'price' in item.custom_fields:
                custom_price = str(item.custom_fields['price'])
            if 'quantity' in item.custom_fields:
                custom_quantity = str(item.custom_fields['quantity'])
            if 'description' in item.custom_fields:
                custom_description = item.custom_fields['description']
            if 'location' in item.custom_fields:
                custom_location = item.custom_fields['location']

        # eBay template column mapping - using exact column names from template
        # Column 3 is the Action column (contains *Action in its name)
        action_col = self._get_action_column()
        row[action_col] = 'Add'

        # Required fields - these match exact column names in the template
        row['*Category'] = '617'  # DVDs & Blu-ray Discs category (updated from 11232)
        row['*Title'] = self._generate_title(item)
        row['*ConditionID'] = self._get_condition_id(item.condition)
        row['*C:Format'] = 'Blu-ray'
        row['*C:Movie/TV Title'] = item.metadata.title if item.metadata else item.title

        # Use custom description if provided, otherwise generate
        if custom_description:
            row['*Description'] = custom_description
        else:
            row['*Description'] = self._generate_description(item)

        row['*Format'] = 'FixedPriceItem'
        row['*Duration'] = 'Days_30'

        # Use custom price if provided, otherwise calculate
        if custom_price:
            row['*StartPrice'] = custom_price
        else:
            row['*StartPrice'] = self._get_price(item)

        row['*Quantity'] = custom_quantity
        row['*Location'] = custom_location
        row['*DispatchTimeMax'] = '1'
        row['*ReturnsAcceptedOption'] = 'ReturnsAccepted'

        # Category-specific fields (C: prefix fields)
        if item.metadata:
            row['C:Studio'] = item.metadata.studio or ''
            row['C:Genre'] = item.metadata.genres[0] if item.metadata.genres else ''
            row['C:Sub-Genre'] = item.metadata.genres[1] if len(item.metadata.genres) > 1 else ''
            row['C:Director'] = item.metadata.director or ''
            row['C:Actor'] = ', '.join(item.metadata.actors[:3]) if item.metadata.actors else ''
            row['C:Release Year'] = self._extract_year(item.metadata.release_date) if item.metadata.release_date else ''
            row['C:Rating'] = item.metadata.rating or ''
            row['C:Run Time'] = str(item.metadata.runtime) if item.metadata.runtime else ''

        # Technical specifications - using exact column names from template
        row['C:Region Code'] = '1'  # US/Canada
        row['C:Language'] = 'English'
        row['C:Case Type'] = 'Standard Blu-ray Case'
        row['C:Country of Origin'] = 'United States'  # Fixed: was "Country/Region of Manufacture"

        # Images
        if item.photos:
            row['PicURL'] = ';'.join(item.photos)
            row['GalleryType'] = 'Gallery'

        # Pricing
        row['BuyItNowPrice'] = row['*StartPrice']
        row['BestOfferEnabled'] = '1'

        price_val = float(row['*StartPrice'])
        # Set auto-accept at 90% of asking price
        auto_accept = round(price_val * 0.9, 2)
        row['BestOfferAutoAcceptPrice'] = str(auto_accept)
        # Set minimum at 75% of asking price
        minimum = round(price_val * 0.75, 2)
        row['MinimumBestOfferPrice'] = str(minimum)

        # Shipping
        row['ShippingType'] = 'Flat'
        row['ShippingService-1:Option'] = 'USPSMedia'
        row['ShippingService-1:Cost'] = '4.99'

        # Returns
        row['ReturnsWithinOption'] = 'Days_30'
        row['RefundOption'] = 'MoneyBack'
        row['ShippingCostPaidByOption'] = 'Buyer'

        return row

    def _generate_title(self, item: BlurayItem) -> str:
        """Generate eBay listing title"""
        if item.metadata and item.metadata.title:
            title = item.metadata.title
            year = self._extract_year(item.metadata.release_date) if item.metadata.release_date else ''

            if year:
                return f"{title} (Blu-ray, {year}) - {item.condition}"
            else:
                return f"{title} (Blu-ray) - {item.condition}"
        else:
            return f"{item.title} (Blu-ray) - {item.condition}"

    def _get_condition_id(self, condition: str) -> str:
        """Convert condition string to eBay condition ID"""
        condition_map = {
            'New': '1000',
            'Like New': '1500',
            'Very Good': '4000',
            'Good': '5000',
            'Acceptable': '6000',
            'Used': '3000'
        }
        return condition_map.get(condition, '3000')

    def _generate_description(self, item: BlurayItem) -> str:
        """Generate HTML description for eBay listing"""
        description = "<div style='font-family: Arial, sans-serif;'>"

        if item.metadata:
            description += f"<h3>{item.metadata.title}</h3>"

            if item.metadata.overview:
                description += f"<p><strong>Plot:</strong> {item.metadata.overview[:200]}...</p>"

            if item.metadata.director:
                description += f"<p><strong>Director:</strong> {item.metadata.director}</p>"

            if item.metadata.actors:
                actors = ', '.join(item.metadata.actors[:5])
                description += f"<p><strong>Cast:</strong> {actors}</p>"

            if item.metadata.genres:
                genres = ', '.join(item.metadata.genres)
                description += f"<p><strong>Genre:</strong> {genres}</p>"

            if item.metadata.runtime:
                description += f"<p><strong>Runtime:</strong> {item.metadata.runtime} minutes</p>"

        description += f"<p><strong>Condition:</strong> {item.condition}</p>"
        description += "<p><strong>Format:</strong> Blu-ray</p>"
        description += "<p><strong>Region:</strong> Region 1 (US/Canada)</p>"

        if item.user_notes:
            description += f"<p><strong>Additional Notes:</strong> {item.user_notes}</p>"

        description += "<p>Fast shipping with tracking. Returns accepted within 30 days.</p>"
        description += "</div>"

        return description

    def _get_price(self, item: BlurayItem) -> str:
        """Get the selling price for the item"""
        if item.price_data and item.price_data.average_price:
            # Use calculated price with margin
            suggested_price = item.price_data.average_price * 1.15
            return f"{suggested_price:.2f}"
        else:
            # Default fallback price
            return "12.99"

    def _extract_year(self, release_date: str) -> str:
        """Extract year from release date string"""
        try:
            return release_date.split('-')[0]
        except:
            return ''

    def create_template_data(self, items: List[BlurayItem]) -> List[Dict[str, Any]]:
        """Create template data for multiple items"""
        template_data = []
        for item in items:
            row = self.create_listing_row(item)
            template_data.append(row)
        return template_data

    def export_to_csv(self, items: List[BlurayItem], output_path: str) -> str:
        """Export items to eBay CSV format"""
        try:
            # Use cached template columns
            template_columns = self._template_columns

            # Create data for all items
            template_data = self.create_template_data(items)

            # Create DataFrame with same columns as template
            df = pd.DataFrame(template_data)

            # Ensure all template columns exist (fill missing with empty strings)
            for col in template_columns:
                if col not in df.columns:
                    df[col] = ''

            # Reorder columns to match template exactly
            df = df.reindex(columns=template_columns, fill_value='')

            # Export to CSV with UTF-8 BOM encoding (eBay requires this)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            return output_path

        except Exception as e:
            raise ValueError(f"Failed to export CSV: {str(e)}")

template_service = TemplateService()