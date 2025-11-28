# eBay Blu-ray MCP Server

An MCP (Model Context Protocol) server for managing eBay Blu-ray listings through conversational AI. Chat with Claude to process images, fetch metadata, and build your eBay bulk upload CSV.

## Features

- **Image Processing**: Upload Blu-ray cover images to AWS S3
- **TMDB Integration**: Automatically fetch movie metadata (title, director, cast, genre, rating, runtime)
- **CSV Management**: Append listings to eBay's File Exchange bulk upload template
- **Conversational Workflow**: Chat naturally to process each disc, confirm prices, handle special cases (steelbooks, region-free, etc.)

## Setup

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager
- [Doppler](https://www.doppler.com/) for secrets management

### Required Environment Variables (via Doppler)

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
S3_BUCKET_NAME
TMDB_READ_TOKEN
```

### Installation

```bash
cd mcp-server
uv sync
```

### Configure Claude Code

The project includes a `.mcp.json` file in the root directory that configures the server:

```json
{
  "mcpServers": {
    "ebay-bluray": {
      "command": "doppler",
      "args": ["run", "--config", "prd", "--", "uv", "run", "ebay-bluray-mcp"],
      "cwd": "/home/ryan/projects/eBay-Blu-Ray-Assist/mcp-server"
    }
  }
}
```

After setup, restart Claude Code to load the MCP server.

## Usage

### Workflow

1. **Add images** to the `mcp-server/images/` folder
2. **Chat with Claude** - "Let's list some Blu-rays"
3. **Process each image** - Claude uploads to S3 and fetches TMDB metadata
4. **Confirm price** - You set the price for each listing
5. **Handle special cases** - Mention steelbooks, region-free discs, condition, etc.
6. **Export CSV** - Get the final file for eBay Seller Hub upload

### Example Conversation

```
You: Let's process the next image

Claude: [Uploads to S3, searches TMDB]
        Found: The Dark Knight (2008)
        Director: Christopher Nolan
        Cast: Christian Bale, Heath Ledger, Aaron Eckhart
        Genre: Action, Crime, Drama
        Rating: PG-13
        Runtime: 152 min

        What price would you like?

You: 9.99

Claude: Added listing #1!
        Title: The Dark Knight (Blu-ray, 2008) - Very Good
        Price: $9.99
        Total listings: 1

You: Next one - this is a steelbook

Claude: [Processes image]
        Found: Inception (2010)
        What price for the steelbook?

You: 14.99

Claude: Added listing #2 as Steelbook!
        Total listings: 2

You: Export the CSV

Claude: Exported 2 listings to:
        ebay_upload_2_items_20241127_143052.csv

        Ready to upload to eBay Seller Hub!
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_images` | Show all images in the upload folder |
| `process_image` | Upload image to S3, fetch TMDB metadata |
| `add_listing` | Add listing to CSV with confirmed price |
| `view_listings` | See all current listings in the CSV |
| `export_csv` | Export final CSV for eBay upload |
| `clear_listings` | Clear all listings and start fresh |
| `view_defaults` | See current default settings |

## Default Settings

These defaults are applied to all listings unless you specify otherwise:

| Setting | Value |
|---------|-------|
| Condition | Very Good (ConditionID: 4000) |
| Location | Los Angeles, CA |
| Shipping | USPS Media Mail @ $4.00 |
| Handling Time | 2 business days |
| Returns | 30 days, buyer pays return shipping |
| Region Code | A/1 (Americas) |
| Case Type | Standard Blu-ray Case |
| Best Offer | Disabled |
| Duration | GTC (Good Till Cancelled) |

### Overriding Defaults

When adding a listing, you can override any default:

- **Condition**: "this one is like new" or "good condition"
- **Case Type**: "steelbook" or "digipak"
- **Region**: "region free" or "region B"
- **Notes**: Any additional info for the description

## File Locations

| Path | Purpose |
|------|---------|
| `mcp-server/images/` | Drop images here to process |
| `backend/.../template/listings_working.csv` | Current working CSV |
| `backend/.../template/ebay_upload_*.csv` | Exported CSVs for eBay |

## Project Structure

```
mcp-server/
├── pyproject.toml              # UV project config
├── .python-version             # Python 3.12
├── README.md                   # This file
├── images/                     # Drop Blu-ray images here
└── src/ebay_bluray_mcp/
    ├── __init__.py
    ├── config.py               # Defaults and environment config
    ├── server.py               # Main MCP server with tools
    └── services/
        ├── __init__.py
        ├── s3_service.py       # AWS S3 image upload
        ├── tmdb_service.py     # TMDB movie metadata
        └── csv_service.py      # eBay CSV management
```

## Troubleshooting

### MCP server not connecting
- Restart Claude Code after adding/modifying `.mcp.json`
- Check Doppler is configured: `doppler secrets --config prd`
- Verify UV installed dependencies: `cd mcp-server && uv sync`

### S3 upload fails
- Verify AWS credentials in Doppler
- Check S3 bucket exists and has public read permissions

### TMDB not finding movies
- Verify `TMDB_READ_TOKEN` in Doppler
- Try specifying the year: "process The Matrix from 1999"
- Check for typos in the movie title

### CSV issues
- The working CSV is at `backend/.../template/listings_working.csv`
- Use `clear_listings` to start fresh if needed
- Exported CSVs are ready for eBay File Exchange upload
