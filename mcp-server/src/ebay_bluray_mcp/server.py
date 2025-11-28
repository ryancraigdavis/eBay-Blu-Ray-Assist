"""MCP server for eBay Blu-ray listing assistant."""

import os
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import config
from .services.s3_service import s3_service
from .services.tmdb_service import tmdb_service, MovieMetadata
from .services.csv_service import csv_service, ListingData

# Get the directory where this script is located
SERVER_DIR = Path(__file__).parent.parent.parent.absolute()

# Initialize the MCP server
server = Server("ebay-bluray-mcp")


def get_images_folder() -> Path:
    """Get the images folder path."""
    return SERVER_DIR / config.images_folder


def get_unprocessed_images() -> list[dict]:
    """Get list of images that haven't been processed yet.

    For now, returns all images. Could track processed images in a JSON file.
    """
    images_folder = get_images_folder()
    if not images_folder.exists():
        images_folder.mkdir(parents=True, exist_ok=True)
        return []

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    images = []

    for file in sorted(images_folder.iterdir()):
        if file.is_file() and file.suffix.lower() in image_extensions:
            images.append({
                "filename": file.name,
                "path": str(file),
                "size_kb": round(file.stat().st_size / 1024, 1),
            })

    return images


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list_images",
            description="List all images in the upload folder waiting to be processed",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="process_image",
            description="Process an image: upload to S3, fetch TMDB metadata. Returns info for you to confirm price.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename of the image to process (from list_images)",
                    },
                    "movie_title": {
                        "type": "string",
                        "description": "Movie title to search TMDB (defaults to filename without extension)",
                    },
                    "year": {
                        "type": "string",
                        "description": "Optional release year to narrow TMDB search",
                    },
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="add_listing",
            description="Add a listing to the CSV after confirming price and details",
            inputSchema={
                "type": "object",
                "properties": {
                    "movie_title": {
                        "type": "string",
                        "description": "Official movie title",
                    },
                    "price": {
                        "type": "string",
                        "description": "Listing price (e.g., '12.99')",
                    },
                    "s3_url": {
                        "type": "string",
                        "description": "S3 URL from process_image",
                    },
                    "condition": {
                        "type": "string",
                        "description": "Condition override (Very Good, Good, Like New, etc.)",
                    },
                    "case_type": {
                        "type": "string",
                        "description": "Case type override (Steelbook, Digipak, Standard Blu-ray Case)",
                    },
                    "region_code": {
                        "type": "string",
                        "description": "Region code override (A, B, C, or Free)",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes for the description",
                    },
                    "metadata_json": {
                        "type": "string",
                        "description": "JSON string of MovieMetadata from process_image",
                    },
                },
                "required": ["movie_title", "price", "s3_url"],
            },
        ),
        Tool(
            name="view_listings",
            description="View all current listings in the CSV",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="export_csv",
            description="Export the final CSV file ready for eBay upload",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional custom filename for the export",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="clear_listings",
            description="Clear all current listings and start fresh",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm clearing",
                    },
                },
                "required": ["confirm"],
            },
        ),
        Tool(
            name="view_defaults",
            description="View current default settings for listings",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "list_images":
            images = get_unprocessed_images()
            if not images:
                return [TextContent(
                    type="text",
                    text=f"No images found in {get_images_folder()}\n\nAdd images to this folder and try again.",
                )]

            result = f"Found {len(images)} image(s) in {get_images_folder()}:\n\n"
            for i, img in enumerate(images, 1):
                result += f"{i}. {img['filename']} ({img['size_kb']} KB)\n"

            return [TextContent(type="text", text=result)]

        elif name == "process_image":
            filename = arguments["filename"]
            movie_title = arguments.get("movie_title")
            year = arguments.get("year")

            # Find the image
            images_folder = get_images_folder()
            image_path = images_folder / filename

            if not image_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Image not found: {filename}\n\nUse list_images to see available images.",
                )]

            result = f"Processing: {filename}\n\n"

            # Upload to S3
            result += "Uploading to S3... "
            try:
                s3_url = s3_service.upload_image(str(image_path))
                result += "Done!\n"
                result += f"S3 URL: {s3_url}\n\n"
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"S3 upload failed: {str(e)}\n\nCheck your AWS credentials in Doppler.",
                )]

            # Search TMDB
            search_title = movie_title or image_path.stem.replace("_", " ").replace("-", " ")
            result += f"Searching TMDB for: {search_title}\n"

            metadata = None
            metadata_json = "{}"
            try:
                metadata = tmdb_service.search_movie(search_title, year)
                if metadata:
                    result += f"\nFound: {metadata.title}"
                    if metadata.release_year:
                        result += f" ({metadata.release_year})"
                    result += "\n"

                    if metadata.director:
                        result += f"Director: {metadata.director}\n"
                    if metadata.actors:
                        result += f"Cast: {', '.join(metadata.actors[:3])}\n"
                    if metadata.genres:
                        result += f"Genre: {', '.join(metadata.genres)}\n"
                    if metadata.rating:
                        result += f"Rating: {metadata.rating}\n"
                    if metadata.runtime:
                        result += f"Runtime: {metadata.runtime} min\n"

                    metadata_json = json.dumps(metadata.to_dict())
                else:
                    result += "No TMDB match found. You can still add the listing manually.\n"
            except Exception as e:
                result += f"TMDB search failed: {str(e)}\n"

            result += "\n---\n"
            result += "Ready to add listing. What price would you like?\n\n"
            result += "To add this listing, use add_listing with:\n"
            result += f'  movie_title: "{metadata.title if metadata else search_title}"\n'
            result += f'  s3_url: "{s3_url}"\n'
            result += '  price: "<your price>"\n'
            if metadata:
                result += f'  metadata_json: \'{metadata_json}\'\n'

            return [TextContent(type="text", text=result)]

        elif name == "add_listing":
            movie_title = arguments["movie_title"]
            price = arguments["price"]
            s3_url = arguments["s3_url"]

            # Parse optional metadata
            metadata = None
            if "metadata_json" in arguments and arguments["metadata_json"]:
                try:
                    meta_dict = json.loads(arguments["metadata_json"])
                    metadata = MovieMetadata(**meta_dict)
                except:
                    pass

            # Build listing data
            listing = ListingData(
                title="",  # Will be generated
                movie_title=movie_title,
                price=price,
                s3_url=s3_url,
                metadata=metadata,
                condition=arguments.get("condition"),
                case_type=arguments.get("case_type"),
                region_code=arguments.get("region_code"),
                notes=arguments.get("notes"),
            )

            # Get condition_id if condition was overridden
            if listing.condition:
                condition_map = {
                    "New": "1000",
                    "Like New": "1500",
                    "Very Good": "4000",
                    "Good": "5000",
                    "Acceptable": "6000",
                    "Used": "3000",
                }
                listing.condition_id = condition_map.get(listing.condition, "4000")

            # Add to CSV
            result_info = csv_service.add_listing(listing)

            count = csv_service.get_listing_count()
            result = f"Added listing #{result_info['row_number']}!\n\n"
            result += f"Title: {result_info['title']}\n"
            result += f"Price: ${price}\n"
            result += f"\nTotal listings in CSV: {count}\n"

            return [TextContent(type="text", text=result)]

        elif name == "view_listings":
            count = csv_service.get_listing_count()
            if count == 0:
                return [TextContent(
                    type="text",
                    text="No listings yet. Use process_image and add_listing to add some!",
                )]

            summaries = csv_service.get_listings_summary()
            result = f"Current listings ({count} total):\n\n"

            for s in summaries:
                result += f"{s['row']}. {s['movie_title']} - ${s['price']}\n"
                result += f"   {s['title']}\n\n"

            result += f"\nCSV file: {csv_service.get_csv_path()}"

            return [TextContent(type="text", text=result)]

        elif name == "export_csv":
            count = csv_service.get_listing_count()
            if count == 0:
                return [TextContent(
                    type="text",
                    text="No listings to export!",
                )]

            filename = arguments.get("filename")
            export_path = csv_service.export_final_csv(filename)

            result = f"Exported {count} listings!\n\n"
            result += f"File: {export_path}\n\n"
            result += "This file is ready to upload to eBay Seller Hub."

            return [TextContent(type="text", text=result)]

        elif name == "clear_listings":
            if not arguments.get("confirm"):
                return [TextContent(
                    type="text",
                    text="To clear all listings, call clear_listings with confirm=true",
                )]

            csv_service.clear_listings()
            return [TextContent(
                type="text",
                text="All listings cleared. Starting fresh!",
            )]

        elif name == "view_defaults":
            d = config.defaults
            result = "Current listing defaults:\n\n"
            result += f"Condition: {d.condition} (ID: {d.condition_id})\n"
            result += f"Location: {d.location}\n"
            result += f"Region Code: {d.region_code}\n"
            result += f"Case Type: {d.case_type}\n"
            result += f"Best Offer: {'Enabled' if d.best_offer_enabled else 'Disabled'}\n"
            result += f"Shipping: {d.shipping_service} @ ${d.shipping_cost}\n"
            result += f"Handling Time: {d.dispatch_time_max} day(s)\n"
            result += f"Returns: {d.returns_within.replace('Days_', '')} days\n"
            result += f"Duration: {d.duration}\n"
            result += f"Category: {d.category_id}\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}",
        )]


async def run_server():
    """Run the MCP server."""
    # Initialize CSV service
    csv_service.initialize(str(SERVER_DIR))

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
