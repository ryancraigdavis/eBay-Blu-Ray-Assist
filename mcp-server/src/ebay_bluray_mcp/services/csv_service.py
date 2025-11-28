"""CSV service for managing eBay listing template."""

import glob
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from ..config import config
from .tmdb_service import MovieMetadata


@dataclass
class ListingData:
    """Data for a single eBay listing."""

    # Required
    title: str
    movie_title: str
    price: str
    s3_url: str

    # From TMDB (optional)
    metadata: Optional[MovieMetadata] = None

    # Overrides (optional) - use defaults if not specified
    condition: Optional[str] = None
    condition_id: Optional[str] = None
    case_type: Optional[str] = None
    region_code: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None


class CSVService:
    """Manage the eBay CSV template and listings."""

    def __init__(self):
        self._template_columns: list[str] = []
        self._csv_path: Optional[str] = None
        self._base_path: Optional[str] = None

    def initialize(self, base_path: str):
        """Initialize service with paths.

        Args:
            base_path: Base path of the MCP server directory
        """
        self._base_path = base_path
        template_dir = config.get_template_path(base_path)

        # Find the eBay template
        template_files = glob.glob(os.path.join(template_dir, "eBay-category-listing-template-*.csv"))
        if not template_files:
            raise ValueError(f"No eBay template CSV found in {template_dir}")

        # Use most recent template
        template_path = max(template_files, key=os.path.getmtime)

        # Load template columns - eBay's format uses \r as line separators
        # We need to read the raw bytes and handle the unusual format
        with open(template_path, "rb") as f:
            content = f.read()

        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]

        # Decode and get just the header portion (before any Info rows that start guidance text)
        text = content.decode("utf-8")

        # The header ends at the first occurrence of "Info,>>>" which starts the guidance rows
        # Everything before that is the header (possibly split by \r)
        guidance_start = text.find("Info,>>>")
        if guidance_start > 0:
            header_section = text[:guidance_start]
        else:
            header_section = text

        # Remove all \r and \n to get clean header line
        header_line = header_section.replace("\r", "").replace("\n", "")

        # Remove trailing commas
        header_line = header_line.rstrip(",")

        # Use pandas to properly parse the header (handles quoted commas)
        import io
        df = pd.read_csv(io.StringIO(header_line + "\n"), nrows=0)
        self._template_columns = list(df.columns)

        # Set up working CSV path (in template directory)
        self._csv_path = os.path.join(template_dir, "listings_working.csv")

        # Create working CSV if it doesn't exist
        if not os.path.exists(self._csv_path):
            self._create_empty_csv()

    def _create_empty_csv(self):
        """Create empty CSV with template headers."""
        df = pd.DataFrame(columns=self._template_columns)
        df.to_csv(self._csv_path, index=False, encoding="utf-8-sig")

    def _get_action_column(self) -> str:
        """Get the Action column name (column 3 in eBay template)."""
        if len(self._template_columns) > 2:
            return self._template_columns[2]
        return "*Action"

    def _generate_listing_title(self, listing: ListingData) -> str:
        """Generate eBay listing title."""
        title = listing.movie_title
        year = ""
        condition = listing.condition or config.defaults.condition

        if listing.metadata and listing.metadata.release_year:
            year = listing.metadata.release_year

        if year:
            return f"{title} (Blu-ray, {year}) - {condition}"
        return f"{title} (Blu-ray) - {condition}"

    def _generate_description(self, listing: ListingData) -> str:
        """Generate HTML description for eBay listing."""
        desc = "<div style='font-family: Arial, sans-serif;'>"

        if listing.metadata:
            desc += f"<h3>{listing.metadata.title}</h3>"

            if listing.metadata.overview:
                overview = listing.metadata.overview[:300]
                if len(listing.metadata.overview) > 300:
                    overview += "..."
                desc += f"<p><strong>Plot:</strong> {overview}</p>"

            if listing.metadata.director:
                desc += f"<p><strong>Director:</strong> {listing.metadata.director}</p>"

            if listing.metadata.actors:
                actors = ", ".join(listing.metadata.actors[:5])
                desc += f"<p><strong>Cast:</strong> {actors}</p>"

            if listing.metadata.genres:
                genres = ", ".join(listing.metadata.genres)
                desc += f"<p><strong>Genre:</strong> {genres}</p>"

            if listing.metadata.runtime:
                desc += f"<p><strong>Runtime:</strong> {listing.metadata.runtime} minutes</p>"

        condition = listing.condition or config.defaults.condition
        desc += f"<p><strong>Condition:</strong> {condition}</p>"
        desc += "<p><strong>Format:</strong> Blu-ray</p>"

        region = listing.region_code or config.defaults.region_code
        desc += f"<p><strong>Region:</strong> Region {region}</p>"

        if listing.notes:
            desc += f"<p><strong>Notes:</strong> {listing.notes}</p>"

        desc += "<p>Fast shipping with tracking. Returns accepted within 30 days.</p>"
        desc += "</div>"

        return desc

    def add_listing(self, listing: ListingData) -> dict:
        """Add a listing to the CSV.

        Args:
            listing: ListingData with all listing information

        Returns:
            Dict with listing details and row number
        """
        if not self._csv_path:
            raise ValueError("CSV service not initialized. Call initialize() first.")

        # Build the row
        row = {col: "" for col in self._template_columns}

        # Action column (column 3)
        action_col = self._get_action_column()
        row[action_col] = "Add"

        # Required fields
        row["*Category"] = config.defaults.category_id
        row["*Title"] = listing.title or self._generate_listing_title(listing)
        row["*ConditionID"] = listing.condition_id or config.defaults.condition_id
        row["*C:Format"] = config.defaults.format
        row["*C:Movie/TV Title"] = listing.movie_title
        row["*Description"] = self._generate_description(listing)
        row["*Format"] = config.defaults.listing_format
        row["*Duration"] = config.defaults.duration
        row["*StartPrice"] = listing.price
        row["*Quantity"] = str(listing.quantity or config.defaults.quantity)
        row["*Location"] = config.defaults.location
        row["*DispatchTimeMax"] = config.defaults.dispatch_time_max
        row["*ReturnsAcceptedOption"] = config.defaults.returns_accepted

        # Category-specific fields from metadata
        if listing.metadata:
            row["C:Studio"] = listing.metadata.studio or ""
            row["C:Genre"] = listing.metadata.genres[0] if listing.metadata.genres else ""
            row["C:Sub-Genre"] = listing.metadata.genres[1] if len(listing.metadata.genres) > 1 else ""
            row["C:Director"] = listing.metadata.director or ""
            row["C:Actor"] = ", ".join(listing.metadata.actors[:3]) if listing.metadata.actors else ""
            row["C:Release Year"] = listing.metadata.release_year or ""
            row["C:Rating"] = listing.metadata.rating or ""
            row["C:Run Time"] = str(listing.metadata.runtime) if listing.metadata.runtime else ""

        # Technical specs
        row["C:Region Code"] = listing.region_code or config.defaults.region_code
        row["C:Language"] = config.defaults.language
        row["C:Case Type"] = listing.case_type or config.defaults.case_type
        row["C:Country of Origin"] = "United States"

        # Image
        row["PicURL"] = listing.s3_url
        row["GalleryType"] = "Gallery"

        # Pricing
        row["BuyItNowPrice"] = listing.price
        row["BestOfferEnabled"] = "1" if config.defaults.best_offer_enabled else "0"

        # Shipping
        row["ShippingType"] = "Flat"
        row["ShippingService-1:Option"] = config.defaults.shipping_service
        row["ShippingService-1:Cost"] = config.defaults.shipping_cost

        # Returns
        row["ReturnsWithinOption"] = config.defaults.returns_within
        row["RefundOption"] = config.defaults.refund_option
        row["ShippingCostPaidByOption"] = config.defaults.return_shipping_paid_by

        # Read existing CSV and append
        df = pd.read_csv(self._csv_path, encoding="utf-8-sig")
        new_row = pd.DataFrame([row])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self._csv_path, index=False, encoding="utf-8-sig")

        return {
            "row_number": len(df),
            "title": row["*Title"],
            "price": listing.price,
            "movie_title": listing.movie_title,
        }

    def get_listing_count(self) -> int:
        """Get number of listings in current CSV."""
        if not self._csv_path or not os.path.exists(self._csv_path):
            return 0
        df = pd.read_csv(self._csv_path, encoding="utf-8-sig")
        return len(df)

    def get_listings_summary(self) -> list[dict]:
        """Get summary of all listings in CSV."""
        if not self._csv_path or not os.path.exists(self._csv_path):
            return []

        df = pd.read_csv(self._csv_path, encoding="utf-8-sig")
        summaries = []

        for idx, row in df.iterrows():
            summaries.append({
                "row": idx + 1,
                "title": row.get("*Title", ""),
                "movie_title": row.get("*C:Movie/TV Title", ""),
                "price": row.get("*StartPrice", ""),
                "condition_id": row.get("*ConditionID", ""),
            })

        return summaries

    def clear_listings(self):
        """Clear all listings (create fresh CSV)."""
        self._create_empty_csv()

    def get_csv_path(self) -> str:
        """Get path to the working CSV file."""
        return self._csv_path or ""

    def export_final_csv(self, filename: Optional[str] = None) -> str:
        """Export final CSV for eBay upload.

        Args:
            filename: Optional custom filename

        Returns:
            Path to exported CSV
        """
        if not self._csv_path or not os.path.exists(self._csv_path):
            raise ValueError("No listings to export")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            count = self.get_listing_count()
            filename = f"ebay_upload_{count}_items_{timestamp}.csv"

        template_dir = config.get_template_path(self._base_path)
        export_path = os.path.join(template_dir, filename)

        # Copy working CSV to export file
        df = pd.read_csv(self._csv_path, encoding="utf-8-sig")
        df.to_csv(export_path, index=False, encoding="utf-8-sig")

        return export_path


# Singleton instance
csv_service = CSVService()
