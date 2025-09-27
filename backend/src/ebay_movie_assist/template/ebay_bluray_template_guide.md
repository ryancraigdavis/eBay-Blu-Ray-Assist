# eBay Blu-ray Listing Template Guide

## Overview
The eBay template you provided is a bulk listing CSV file with **93 columns** designed for DVD/Blu-ray/Movie category listings. Here's everything you need to know to efficiently list your discounted Blu-rays.

## Template Structure
- **14 Required fields** (marked with `*`)
- **27 Category-specific fields** for movies/Blu-rays (marked with `C:`)
- **52 Optional fields** for pricing, shipping, images, and other details

---

## 🔴 REQUIRED FIELDS (Must Fill)

### Basic Listing Requirements
1. **`*Action`** - Set to "Add" for new listings
2. **`*Category`** - Use category ID for DVDs & Movies (likely 11232 or similar)
3. **`*Title`** - Your listing title (e.g., "The Dark Knight Blu-ray 2008 Christopher Nolan")
4. **`*ConditionID`** - Condition codes:
   - `1000` = New
   - `1500` = New other
   - `3000` = Used
   - `4000` = Very Good
   - `5000` = Good
   - `6000` = Acceptable

### Movie-Specific Required Fields
5. **`*C:Format`** - Set to "Blu-ray"
6. **`*C:Movie/TV Title`** - Official movie title (e.g., "The Dark Knight")

### Listing Details
7. **`*Description`** - HTML description of your item
8. **`*Format`** - Listing format ("FixedPriceItem" for Buy It Now)
9. **`*Duration`** - Listing duration ("Days_30", "Days_7", etc.)
10. **`*StartPrice`** - Your selling price in dollars (e.g., 12.99)
11. **`*Quantity`** - Number of copies you have
12. **`*Location`** - Your city, state (e.g., "Los Angeles, CA")

### Fulfillment Requirements
13. **`*DispatchTimeMax`** - Handling time in days (1, 2, 3, etc.)
14. **`*ReturnsAcceptedOption`** - "ReturnsAccepted" or "ReturnsNotAccepted"

---

## 🎬 CATEGORY-SPECIFIC FIELDS (Highly Recommended for Blu-rays)

### Essential Movie Information
- **`C:Studio`** - Movie studio (Warner Bros, Disney, etc.)
- **`C:Genre`** - Primary genre (Action, Drama, Comedy, etc.)
- **`C:Sub-Genre`** - Secondary genre if applicable
- **`C:Director`** - Director name(s)
- **`C:Actor`** - Main actors (comma-separated)
- **`C:Release Year`** - Original theatrical release year
- **`C:Rating`** - MPAA rating (G, PG, PG-13, R, etc.)

### Technical Specifications
- **`C:Region Code`** - Usually "1" for US/Canada Blu-rays
- **`C:Language`** - Primary language (English, Spanish, etc.)
- **`C:Subtitle Language`** - Available subtitle languages
- **`C:Case Type`** - "Standard Blu-ray Case", "Steelbook", etc.
- **`C:Features`** - Special features (Director Commentary, Deleted Scenes, etc.)
- **`C:Run Time`** - Movie length in minutes

### Additional Details
- **`C:Edition`** - Special edition type (Director's Cut, Extended, etc.)
- **`C:Franchise`** - Series name if applicable (Marvel, DC, etc.)
- **`C:Country/Region of Manufacture`** - Usually "United States"

---

## 📸 IMAGE FIELDS (Critical for Sales)

### Primary Images
- **`PicURL`** - **This is where your S3 bucket URLs go!**
  - Format: Direct image URLs separated by semicolons
  - Example: `https://your-s3-bucket.s3.amazonaws.com/bluray1-front.jpg;https://your-s3-bucket.s3.amazonaws.com/bluray1-back.jpg`
  - eBay supports up to 12 images per listing

### Gallery Options
- **`GalleryType`** - Options:
  - `Gallery` = Standard thumbnail
  - `Plus` = Enlarged gallery image
  - `PicturePack` = Multiple gallery images

---

## 💰 PRICING FIELDS

### Core Pricing
- **`BuyItNowPrice`** - Fixed price (same as StartPrice for Buy It Now)
- **`BestOfferEnabled`** - "1" to allow offers, "0" to disable

### Best Offer Settings (if enabled)
- **`BestOfferAutoAcceptPrice`** - Price that auto-accepts offers
- **`MinimumBestOfferPrice`** - Lowest offer you'll consider

---

## 📦 SHIPPING FIELDS

### Basic Shipping
- **`ShippingType`** - Usually "Flat" for fixed shipping costs
- **`ShippingService-1:Option`** - Primary service (e.g., "USPSMedia", "UPSGround")
- **`ShippingService-1:Cost`** - Cost in dollars (e.g., 4.99)

### Additional Services
- **`ShippingService-2:Option`** - Optional expedited service
- **`ShippingService-2:Cost`** - Cost for expedited shipping

---

## 🔄 RETURNS POLICY

### Basic Returns
- **`ReturnsWithinOption`** - Return window ("Days_30", "Days_60")
- **`RefundOption`** - "MoneyBack" typically
- **`ShippingCostPaidByOption`** - "Buyer" or "Seller"

---

## 📋 QUICK SETUP TEMPLATE FOR BLU-RAYS

Here's a minimal viable template row for a typical Blu-ray:

| Field | Example Value | Notes |
|-------|---------------|-------|
| `*Action` | Add | For new listings |
| `*Category` | 11232 | DVD/Movie category |
| `*Title` | The Dark Knight (Blu-ray, 2008) | Include format and year |
| `*ConditionID` | 3000 | Used condition |
| `*C:Format` | Blu-ray | Always "Blu-ray" |
| `*C:Movie/TV Title` | The Dark Knight | Official title |
| `C:Studio` | Warner Bros | Publisher/Studio |
| `C:Genre` | Action | Primary genre |
| `C:Director` | Christopher Nolan | Director name |
| `C:Release Year` | 2008 | Release year |
| `C:Rating` | PG-13 | MPAA rating |
| `C:Region Code` | 1 | US/Canada |
| `PicURL` | https://your-s3.../front.jpg | Your S3 image URLs |
| `*Description` | Great condition Blu-ray... | HTML description |
| `*Format` | FixedPriceItem | Buy It Now format |
| `*Duration` | Days_30 | 30-day listing |
| `*StartPrice` | 12.99 | Your price |
| `*Quantity` | 1 | Number available |
| `*Location` | Los Angeles, CA | Your location |
| `*DispatchTimeMax` | 1 | 1-day handling |
| `*ReturnsAcceptedOption` | ReturnsAccepted | Accept returns |

---

## 🚀 BEST PRACTICES FOR YOUR BLU-RAY BUSINESS

### 1. Image Strategy with S3
- Take high-quality photos of front cover, back cover, and disc
- Upload to S3 with descriptive filenames
- Use direct S3 URLs in `PicURL` field (semicolon-separated)
- Ensure images are web-optimized (< 1MB each)

### 2. Pricing Strategy
- Research sold listings for comparable titles
- Use `BestOfferEnabled` to increase sales velocity
- Set `BestOfferAutoAcceptPrice` at 85-90% of asking price

### 3. Shipping Efficiency
- Use calculated shipping or flat rate
- Consider eBay Managed Delivery for streamlined fulfillment
- Set realistic handling times (`*DispatchTimeMax`)

### 4. Bulk Listing Tips
- Use Excel or Google Sheets to prepare your data
- Copy/paste common fields across multiple listings
- Test with 1-2 listings before doing bulk upload

### 5. Category-Specific Optimization
- Always fill `C:Studio`, `C:Genre`, `C:Director` for better searchability
- Include `C:Actor` for popular stars
- Use `C:Features` to highlight special content (Director's Commentary, etc.)

---

## ⚠️ IMPORTANT NOTES

1. **Required Fields**: All fields marked with `*` must be filled or eBay will reject the listing
2. **Category Validation**: Make sure your category ID is correct for movies/Blu-rays
3. **Image Requirements**: eBay requires at least one image per listing
4. **S3 Permissions**: Ensure your S3 bucket allows public read access for the images
5. **File Format**: Save as CSV with UTF-8 encoding
6. **Testing**: Always test with a few listings before bulk uploading hundreds

This template will help you efficiently list your discounted Blu-ray inventory while maximizing visibility and sales potential!