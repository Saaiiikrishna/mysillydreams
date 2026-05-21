#!/usr/bin/env python3
"""
SpaceKart OpenProject Scrum Setup Script
=========================================
Creates the SpaceKart project (if needed) and populates all 75 user stories
into their correct sprints via the OpenProject API v3.

Usage:
  # Step 1 - create project + print manual instructions
  python setup_spacekart_project.py

  # After completing manual steps (Backlogs enabled + 6 sprints created):
  python setup_spacekart_project.py --stories

Environment variables required:
  OPENPROJECT_TOKEN   - API token (opapi-...)
  OPENPROJECT_URL     - Base URL (default: https://pm.mysillydreams.com)
"""

import os
import sys
import json
import time
import argparse
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("OPENPROJECT_URL", "https://pm.mysillydreams.com").rstrip("/")
TOKEN    = os.environ.get("OPENPROJECT_TOKEN", "")
PROJECT_IDENTIFIER = "spacekart"

SPRINT_NAMES = [
    "Sprint 0 - Foundation",
    "Sprint 1 - Auth & Identity",
    "Sprint 2 - Catalog & Discovery",
    "Sprint 3 - Orders & Payments",
    "Test Sprint 1 - Integration",
    "Test Sprint 2 - E2E & Performance",
]

CATEGORIES = ["Customer", "Vendor", "Rider", "Staff", "Admin", "AI Wicky"]

# ---------------------------------------------------------------------------
# All 75 user stories
# Fields: id, sprint (None = product backlog), module, epic, subject, story,
#         acceptance, tech_notes, mobile, priority
# Priority: "High" | "Normal" | "Low"
# ---------------------------------------------------------------------------
STORIES = [
    # ── AI WICKY ──────────────────────────────────────────────────────────
    {
        "id": "AIW-001", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "AI Wicky", "epic": "Voice Shopping",
        "subject": "Voice product search",
        "story": "User can search products using voice",
        "acceptance": "Voice converts to text; results are accurate",
        "tech_notes": "Use STT (OpenAI/Whisper), integrate with product search API",
        "mobile": "Yes", "priority": "High",
    },
    {
        "id": "AIW-002", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "AI Wicky", "epic": "Voice Shopping",
        "subject": "Voice add-to-cart",
        "story": "User can add items to cart via voice",
        "acceptance": "Correct item and quantity added after confirmation",
        "tech_notes": "NLP intent + entity extraction; call cart API",
        "mobile": "Yes", "priority": "High",
    },
    {
        "id": "AIW-003", "sprint": "Sprint 3 - Orders & Payments",
        "module": "AI Wicky", "epic": "Voice Shopping",
        "subject": "Voice checkout",
        "story": "User can checkout using voice",
        "acceptance": "Order placed successfully with confirmation",
        "tech_notes": "Integrate payment API + voice confirmation flow",
        "mobile": "Yes", "priority": "High",
    },
    {
        "id": "AIW-004", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "AI Wicky", "epic": "AI Assistant",
        "subject": "Conversation context memory",
        "story": "System maintains conversation context",
        "acceptance": "Follow-up queries understood correctly",
        "tech_notes": "Session memory + LLM context window",
        "mobile": "Yes", "priority": "Normal",
    },
    {
        "id": "AIW-005", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "AI Wicky", "epic": "AI Assistant",
        "subject": "Smart product recommendations",
        "story": "System provides smart recommendations",
        "acceptance": "Relevant suggestions based on history",
        "tech_notes": "Recommendation engine + past orders",
        "mobile": "Yes", "priority": "Normal",
    },
    {
        "id": "AIW-006", "sprint": "Sprint 3 - Orders & Payments",
        "module": "AI Wicky", "epic": "Order Support",
        "subject": "Voice order tracking",
        "story": "User can track order via voice",
        "acceptance": "Returns real-time order status and ETA",
        "tech_notes": "Integrate delivery API + maps",
        "mobile": "Yes", "priority": "High",
    },
    {
        "id": "AIW-007", "sprint": None,
        "module": "AI Wicky", "epic": "Order Support",
        "subject": "Voice order cancel/modify",
        "story": "User can cancel/modify order via voice",
        "acceptance": "Order updated or cancelled with confirmation",
        "tech_notes": "Order service validation + status check",
        "mobile": "Yes", "priority": "High",
    },
    {
        "id": "AIW-008", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "AI Wicky", "epic": "Seller AI",
        "subject": "Vendor voice inventory update",
        "story": "Seller updates inventory via voice",
        "acceptance": "Inventory updated correctly",
        "tech_notes": "Speech-to-text + product update API",
        "mobile": "Yes", "priority": "Normal",
    },
    {
        "id": "AIW-009", "sprint": None,
        "module": "AI Wicky", "epic": "Rider AI",
        "subject": "Rider voice navigation support",
        "story": "Rider gets voice navigation support",
        "acceptance": "Provides optimized route and ETA",
        "tech_notes": "Google Maps API + voice assistant",
        "mobile": "Yes", "priority": "Normal",
    },
    {
        "id": "AIW-010", "sprint": "Sprint 1 - Auth & Identity",
        "module": "AI Wicky", "epic": "AI Core",
        "subject": "AI intent classification (>=90% accuracy)",
        "story": "System detects user intent",
        "acceptance": "Intent classification accuracy >=90%",
        "tech_notes": "LLM/NLP model for intent classification",
        "mobile": "No", "priority": "High",
    },
    {
        "id": "AIW-011", "sprint": "Sprint 1 - Auth & Identity",
        "module": "AI Wicky", "epic": "AI Core",
        "subject": "AI entity extraction (product + quantity)",
        "story": "System extracts entities from input",
        "acceptance": "Correct product, quantity extracted",
        "tech_notes": "NER model + parsing logic",
        "mobile": "No", "priority": "High",
    },
    {
        "id": "AIW-012", "sprint": None,
        "module": "AI Wicky", "epic": "Admin",
        "subject": "Admin AI interaction logs",
        "story": "Admin can view AI interaction logs",
        "acceptance": "Logs stored and searchable",
        "tech_notes": "DB logging + admin dashboard",
        "mobile": "No", "priority": "Normal",
    },
    {
        "id": "AIW-013", "sprint": "Sprint 1 - Auth & Identity",
        "module": "AI Wicky", "epic": "Security",
        "subject": "Secure voice transactions (JWT + OTP)",
        "story": "System secures voice transactions",
        "acceptance": "OTP and auth validation successful",
        "tech_notes": "JWT + OTP service integration",
        "mobile": "Yes", "priority": "High",
    },

    # ── CUSTOMER ──────────────────────────────────────────────────────────
    {
        "id": "CUS-001", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Customer", "epic": "Auth & Onboarding",
        "subject": "Mobile number OTP signup",
        "story": "I'm a new customer and I want to sign up using my mobile number, so I can start shopping without needing an email address.",
        "acceptance": "1. Mobile number field accepts 10-digit Indian numbers only.\n2. OTP sent within 5 sec via SMS.\n3. Wrong format shows 'Enter a valid 10-digit mobile number'.\n4. Account created after OTP verified.\n5. Duplicate number shows 'Already registered. Want to login?'",
        "tech_notes": "Node.js + Twilio/MSG91; E.164 format stored; JWT on success",
        "mobile": "Regex: ^[6-9]\\d{9}$; Masked display; OTP auto-read (Android OTP API)",
        "priority": "High",
    },
    {
        "id": "CUS-002", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Customer", "epic": "Auth & Onboarding",
        "subject": "Mobile OTP login",
        "story": "I want to log in with my mobile number and OTP so I don't have to remember a password.",
        "acceptance": "1. OTP valid for 5 minutes.\n2. Max 3 wrong OTP attempts then 30-min lockout.\n3. Resend OTP available after 30 sec.\n4. On success, JWT + refresh token issued.",
        "tech_notes": "Redis OTP store with TTL; bcrypt not needed (OTP-based)",
        "mobile": "Phone field auto-fills last used number; keypad shown on focus",
        "priority": "High",
    },
    {
        "id": "CUS-003", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Customer", "epic": "Auth & Onboarding",
        "subject": "Google OAuth login",
        "story": "I want to sign in with Google so I can get started even faster.",
        "acceptance": "1. Google OAuth redirects back to app.\n2. If mobile not linked, prompt to add mobile number.\n3. Mobile verified via OTP before account activated.",
        "tech_notes": "Passport.js Google strategy; merge accounts if same email",
        "mobile": "Post-OAuth: mobile number mandatory before first order",
        "priority": "High",
    },
    {
        "id": "CUS-004", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Customer", "epic": "Auth & Onboarding",
        "subject": "Delivery address management (up to 5 addresses)",
        "story": "I want to add and manage my delivery addresses so I can ship to home, office, or anywhere I choose.",
        "acceptance": "1. Up to 5 saved addresses.\n2. Fields: label, full address, pincode, landmark.\n3. Default address pre-selected at checkout.\n4. Pincode validated against serviceable areas.",
        "tech_notes": "MSSQL: CustomerAddresses table; Azure Maps for pincode lookup",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-005", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Customer", "epic": "Product Discovery",
        "subject": "Product search + filter (price, category, rating, distance)",
        "story": "I want to search for products and filter by price, category, rating, and distance so I can quickly find exactly what I need.",
        "acceptance": "1. Results load within 1 second.\n2. Filters: category, price range, star rating, within N km.\n3. Spelling tolerance (fuzzy match).\n4. No results shows suggestions.",
        "tech_notes": "SQL Full-Text Search or Azure Cognitive Search; geo-filter on lat/lng",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-006", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Customer", "epic": "Product Discovery",
        "subject": "Category browsing (3-level tree with breadcrumb)",
        "story": "I want to browse products by category so I can explore what's available without knowing exactly what to search for.",
        "acceptance": "1. Category tree up to 3 levels deep.\n2. Sub-categories shown on drill-down.\n3. Product count shown per category.\n4. Breadcrumb trail visible.",
        "tech_notes": "MSSQL: Categories (parent_id self-ref); cached in Redis",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-007", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Customer", "epic": "Product Discovery",
        "subject": "Full product detail page (images, specs, seller info)",
        "story": "I want to see full product details — images, specs, and seller info — so I can make a confident buying decision.",
        "acceptance": "1. Image carousel with zoom (min 3 images).\n2. Specs shown in key-value table.\n3. Seller name, rating, avg response time visible.\n4. In-stock / Out-of-stock badge.",
        "tech_notes": "Azure Blob Storage for images; signed CDN URLs",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-008", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Customer", "epic": "Product Discovery",
        "subject": "Wishlist (up to 50 items, persists across devices)",
        "story": "I want to save products to my wishlist so I can come back to them later without losing track.",
        "acceptance": "1. Heart icon toggles wishlist.\n2. Wishlist persists across devices.\n3. Out-of-stock items marked but not removed.\n4. Max 50 items.",
        "tech_notes": "MSSQL: Wishlists table; synced per session",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "CUS-009", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Customer", "epic": "Product Discovery",
        "subject": "Deals, promo banners & product recommendations",
        "story": "I want to see deals, promo banners, and similar product recommendations so I can discover great value and alternatives.",
        "acceptance": "1. Homepage banners configurable by admin.\n2. Promo code shown on product page if applicable.\n3. Similar products section shows >=4 items.\n4. Recommendations based on same category + price band.",
        "tech_notes": "Rule-based recommendation engine; banner images in Azure Blob",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "CUS-010", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Cart & Checkout",
        "subject": "Cart management with real-time total",
        "story": "I want to add items to my cart, adjust quantities, and see the running total so I know exactly what I'm about to spend.",
        "acceptance": "1. Add/remove/change qty.\n2. Price updates in real-time.\n3. Cart persists after browser close.\n4. Stock check on checkout — if OOS, warn before payment.",
        "tech_notes": "MSSQL: CartItems; real-time price via API call on qty change",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-011", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Cart & Checkout",
        "subject": "Promo code application at checkout",
        "story": "I want to apply a promo code at checkout so I can get the discount I'm entitled to.",
        "acceptance": "1. Code validated server-side (not client).\n2. Discount shown immediately.\n3. Expired or invalid code shows clear error.\n4. Only one code per order.",
        "tech_notes": "MSSQL: PromoCodes table with usage_count, max_uses, expiry",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-012", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Cart & Checkout",
        "subject": "Delivery option selection (same-city fast vs standard)",
        "story": "I want to choose between same-city fast delivery (Ola/Rapido/Uber) or standard delivery so I can pick what suits me.",
        "acceptance": "1. Same-city option shown only if vendor within configured radius.\n2. Estimated delivery time shown for each option.\n3. Delivery cost shown before payment.",
        "tech_notes": "Ola/Rapido/Uber API integration; Google Maps Distance Matrix for ETA",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-013", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Payments",
        "subject": "Multi-method payment (UPI / card / wallet / COD)",
        "story": "I want to pay via UPI, card, digital wallet, or Cash on Delivery so I always have a payment option I'm comfortable with.",
        "acceptance": "1. Razorpay/PayU integration for UPI, card, wallet.\n2. COD available only in serviceable zones.\n3. Payment page is PCI-DSS compliant.\n4. 3D Secure for card payments.",
        "tech_notes": "Razorpay Node.js SDK; webhook for payment confirmation; idempotency key",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-014", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Payments",
        "subject": "Instant order confirmation + digital receipt",
        "story": "I want to receive an instant order confirmation and digital receipt after I pay so I have proof of purchase.",
        "acceptance": "1. Confirmation screen within 5 sec of payment.\n2. Email receipt sent automatically.\n3. Receipt includes: order ID, items, amounts, timestamp, payment method.",
        "tech_notes": "Azure SendGrid for email; MSSQL: OrderReceipts table",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-015", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Payments",
        "subject": "Refund request for cancelled or problematic orders",
        "story": "I want to request a refund for a cancelled or problematic order so I get my money back without hassle.",
        "acceptance": "1. Refund request from order history.\n2. Reason required (dropdown + optional note).\n3. Auto-refund triggered via Razorpay if eligible.\n4. Refund status visible in app; email on completion.",
        "tech_notes": "Razorpay Refund API; MSSQL: Refunds table with status tracking",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-016", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Order Management",
        "subject": "Live map order tracking (Socket.io + GPS, 5-sec updates)",
        "story": "I want to track my order live on a map so I know exactly where my delivery is and when it will arrive.",
        "acceptance": "1. Rider location updates every 5 seconds.\n2. ETA recalculates in real time.\n3. Map shows pickup point, rider, and my address.\n4. Rider contact number shown (masked).",
        "tech_notes": "Socket.io for live updates; Google Maps JS SDK; rider GPS via mobile",
        "mobile": "Rider phone: tap-to-call from order screen; number masked as +91-XXXXX-12345",
        "priority": "High",
    },
    {
        "id": "CUS-017", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Order Management",
        "subject": "Push notifications for all order status changes",
        "story": "I want to get push notifications at every order status change so I'm never left wondering what's happening.",
        "acceptance": "1. Notifications for: Confirmed, Packed, Rider Assigned, Out for Delivery, Delivered.\n2. Tapping notification opens the relevant order.\n3. Notifications work even when app is closed.",
        "tech_notes": "Firebase Cloud Messaging (FCM); MSSQL: NotificationLog",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-018", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Customer", "epic": "Order Management",
        "subject": "Order cancellation before packing",
        "story": "I want to cancel my order before it's packed so I don't end up paying for something I no longer need.",
        "acceptance": "1. Cancel button visible if status is 'Confirmed'.\n2. Cancellation reason required.\n3. Prepaid orders auto-refunded.\n4. COD orders simply closed.",
        "tech_notes": "Status state-machine in Node.js service; refund triggered if paid",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-019", "sprint": None,
        "module": "Customer", "epic": "Order Management",
        "subject": "Order history + one-tap reorder",
        "story": "I want to view my complete order history and easily reorder past purchases so I can buy my favourites quickly.",
        "acceptance": "1. All orders listed newest first.\n2. Filter by status, date range.\n3. One-tap 'Reorder' adds all items to cart.\n4. Items no longer available shown as unavailable.",
        "tech_notes": "MSSQL: Orders, OrderItems with vendor_id join",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "CUS-020", "sprint": None,
        "module": "Customer", "epic": "Order Management",
        "subject": "Product return & exchange within 7-day window",
        "story": "I want to return or exchange a product within the return window so I can fix a problem with my purchase.",
        "acceptance": "1. Return option available within 7 days of delivery.\n2. Reason + photo upload required.\n3. Return status: Requested -> Picked Up -> Refunded.\n4. Vendor and admin notified.",
        "tech_notes": "Azure Blob for return photos; MSSQL: Returns table",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "CUS-021", "sprint": None,
        "module": "Customer", "epic": "AI Voice (Wicky)",
        "subject": "Hands-free voice shopping (English + Hindi)",
        "story": "I want to search and add products to my cart using my voice so I can shop completely hands-free.",
        "acceptance": "1. Mic button activates voice capture.\n2. Spoken product name matched against catalog.\n3. Cart updated with voice confirmation read back.\n4. Works in English and Hindi.",
        "tech_notes": "OpenAI Whisper for STT; GPT function-calling for intent; Google TTS for response",
        "mobile": "Mic permission prompt on first use; background noise filter",
        "priority": "Low",
    },

    # ── VENDOR ────────────────────────────────────────────────────────────
    {
        "id": "VEN-001", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Vendor", "epic": "Onboarding & KYC",
        "subject": "Vendor business registration + GST/PAN/bank doc upload",
        "story": "I'm a vendor and I want to register my business with my GST, PAN, and bank details so I can start selling on SpaceKart.",
        "acceptance": "1. Fields: business name, GST, PAN, address, bank IFSC + account.\n2. Document upload: GST cert, PAN, shop license (PDF/JPEG <=5MB each).\n3. Submission triggers KYC review by admin.\n4. Reference number issued immediately.",
        "tech_notes": "Azure Blob for docs; MSSQL: Vendors, VendorDocuments; status enum",
        "mobile": "Mobile number verified via OTP before KYC form shown; stored as primary contact",
        "priority": "High",
    },
    {
        "id": "VEN-002", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Vendor", "epic": "Onboarding & KYC",
        "subject": "Vendor KYC approval status tracking",
        "story": "I want to track my KYC approval status so I know when I can go live.",
        "acceptance": "1. Status: Pending Review / Approved / Rejected (with reason).\n2. Email + SMS notification on status change.\n3. If rejected, re-upload option available.",
        "tech_notes": "MSSQL: KYCStatus; Azure SendGrid + SMS on update",
        "mobile": "SMS sent to registered mobile on every status change",
        "priority": "High",
    },
    {
        "id": "VEN-003", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Vendor", "epic": "Onboarding & KYC",
        "subject": "Vendor store profile (logo, description, hours, location)",
        "story": "I want to create my store profile with a logo, description, and operating hours so customers can trust and recognise my shop.",
        "acceptance": "1. Logo upload <=2MB (PNG/JPG).\n2. Description max 500 chars.\n3. Operating hours per day of week.\n4. Store location pinned on map.",
        "tech_notes": "Azure Blob CDN for logo; MSSQL: VendorProfiles",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "VEN-004", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Vendor", "epic": "Product Management",
        "subject": "Add products (images, pricing, stock, SKU)",
        "story": "I want to add new products with images, pricing, and stock count so customers can browse and buy them.",
        "acceptance": "1. Title, description, category, price, stock required.\n2. Up to 10 product images.\n3. SKU auto-generated if not provided.\n4. Save as Draft or Publish immediately.",
        "tech_notes": "Azure Blob for images; MSSQL: Products, ProductImages",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "VEN-005", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Vendor", "epic": "Product Management",
        "subject": "Bulk CSV catalog upload (up to 500 products)",
        "story": "I want to bulk upload my entire product catalog using a CSV template so I can go live quickly without adding items one by one.",
        "acceptance": "1. Template downloadable from dashboard.\n2. CSV validated row-by-row; errors listed before import.\n3. Max 500 products per upload.\n4. Images linked via URL in CSV.",
        "tech_notes": "Node.js stream CSV parser (csv-parse); background job for large files",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "VEN-006", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Vendor", "epic": "Product Management",
        "subject": "Real-time stock management + low-stock alerts",
        "story": "I want to manage my stock levels in real-time so I never accidentally accept an order for something I don't have.",
        "acceptance": "1. Stock decrements automatically on order confirmation.\n2. Low-stock alert at configurable threshold (default: 5).\n3. Out-of-stock hides product from buyer search.\n4. Manual stock edit available.",
        "tech_notes": "MSSQL: Products.stock_qty with optimistic locking on concurrent orders",
        "mobile": "Push notification when stock falls below threshold",
        "priority": "High",
    },
    {
        "id": "VEN-007", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Vendor", "epic": "Product Management",
        "subject": "Discount pricing & time-limited promotions",
        "story": "I want to set discount prices and run time-limited promotions so I can attract more customers during peak periods.",
        "acceptance": "1. Discount as % or flat amount.\n2. Start and end date/time for sale.\n3. Strikethrough original price shown to buyer.\n4. Auto-reverts to original price after sale ends.",
        "tech_notes": "MSSQL: ProductPricing with effective_from, effective_to; scheduled Azure Function",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "VEN-008", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Vendor", "epic": "Order Management",
        "subject": "New order push notification + audio alert",
        "story": "I want to receive an instant notification for every new order so I can start preparing it right away.",
        "acceptance": "1. Push + in-app alert with order summary.\n2. Audio alert when app is open.\n3. Order detail accessible in one tap.",
        "tech_notes": "FCM; MSSQL: Orders; vendor_id filtered",
        "mobile": "Push to vendor's registered mobile number",
        "priority": "High",
    },
    {
        "id": "VEN-009", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Vendor", "epic": "Order Management",
        "subject": "Accept/reject order (15-minute auto-cancel)",
        "story": "I want to accept or reject an incoming order within 15 minutes so customers aren't kept waiting.",
        "acceptance": "1. Accept / Reject buttons on order card.\n2. Rejection requires a reason.\n3. Customer notified immediately on either action.\n4. Unactioned orders auto-cancelled after 15 min.",
        "tech_notes": "Azure Timer Function for auto-cancel; Socket.io for real-time customer update",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "VEN-010", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Vendor", "epic": "Order Management",
        "subject": "Order status step updates (Accepted -> Packed -> Ready)",
        "story": "I want to update the order status step by step (Accepted -> Packed -> Ready for Pickup) so customers and riders always know what's happening.",
        "acceptance": "1. Status buttons shown in sequence; can't skip steps.\n2. Each status change triggers customer + rider notification.\n3. Timestamp logged per status.",
        "tech_notes": "MSSQL: OrderStatusHistory; FCM on each transition",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "VEN-011", "sprint": None,
        "module": "Vendor", "epic": "Order Management",
        "subject": "Shipping label PDF printing (QR code + order details)",
        "story": "I want to print a shipping label for each order so I can pack and hand over to the rider without confusion.",
        "acceptance": "1. PDF label with: order ID, customer name + address, items list, QR code.\n2. Printable from browser.\n3. Available immediately after order acceptance.",
        "tech_notes": "pdfkit / jsPDF in Node.js; Azure Blob for label storage",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "VEN-012", "sprint": None,
        "module": "Vendor", "epic": "Dashboard & Analytics",
        "subject": "Vendor sales dashboard (GMV, orders, top products)",
        "story": "I want a sales dashboard that shows me today's revenue, order count, and top products so I can make quick business decisions.",
        "acceptance": "1. Cards: Today GMV, Orders, Avg order value, Revenue after commission.\n2. Period toggle: Today / This week / This month.\n3. Top 5 products by revenue shown.",
        "tech_notes": "MSSQL aggregation queries; React Chart.js; cached every 5 min",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "VEN-013", "sprint": None,
        "module": "Vendor", "epic": "Dashboard & Analytics",
        "subject": "Sales report Excel export (date range, per order)",
        "story": "I want to download my sales reports as Excel files so I can share them with my accountant or do my own analysis.",
        "acceptance": "1. Date range selector.\n2. Export includes: date, order ID, product, qty, revenue, commission, net payout.\n3. Exported as .xlsx file.",
        "tech_notes": "exceljs in Node.js; streamed response for large files",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "VEN-014", "sprint": None,
        "module": "Vendor", "epic": "Payouts",
        "subject": "Earnings & commission breakdown with payout history",
        "story": "I want to see a clear breakdown of my earnings and commission deductions so I always know exactly what I'll receive in my bank account.",
        "acceptance": "1. Per-order: gross amount, platform commission %, net amount.\n2. Payout schedule shown (e.g. weekly every Monday).\n3. Payout history with bank reference number.",
        "tech_notes": "MSSQL: Payouts, CommissionConfig; Razorpay Payouts API",
        "mobile": "SMS on every payout credit",
        "priority": "High",
    },

    # ── STAFF ─────────────────────────────────────────────────────────────
    {
        "id": "STA-001", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Staff", "epic": "Auth & Access",
        "subject": "Staff login with RBAC (role-based menu access)",
        "story": "As a staff member, I want to log in with my assigned credentials and only see the sections I'm permitted to access, so sensitive data is protected.",
        "acceptance": "1. Staff login with email + password (no OTP — internal use).\n2. Role-based menu: only permitted modules shown.\n3. Session expires after 8 hours of inactivity.\n4. Failed logins locked after 5 attempts.",
        "tech_notes": "MSSQL: Staff, StaffRoles, Permissions; JWT with role claims; RBAC middleware",
        "mobile": "Mobile number stored for internal alerts only; no OTP login",
        "priority": "High",
    },
    {
        "id": "STA-002", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Staff", "epic": "Order Operations",
        "subject": "Live order board (all vendors, filter by status/vendor)",
        "story": "I want to view all live orders across all vendors so I can monitor fulfilment and step in if something is stuck.",
        "acceptance": "1. Live order board with status columns.\n2. Filter by vendor, status, delivery type.\n3. Orders stuck in a status > 30 min highlighted in red.\n4. Can add internal notes to any order.",
        "tech_notes": "Socket.io for live board; MSSQL: Orders with vendor join; Redis for stuck-order alerts",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "STA-003", "sprint": None,
        "module": "Staff", "epic": "Order Operations",
        "subject": "Manual rider reassignment when original rider cancels",
        "story": "I want to manually reassign a rider to an order if the original rider cancels, so deliveries aren't left stranded.",
        "acceptance": "1. Rider reassignment from order detail screen.\n2. Only online, available riders shown.\n3. New rider notified via push + SMS.\n4. Customer notified of rider change.",
        "tech_notes": "MSSQL: OrderRiderAssignments; FCM to new rider; customer notification",
        "mobile": "SMS to new rider's registered mobile on assignment",
        "priority": "High",
    },
    {
        "id": "STA-004", "sprint": None,
        "module": "Staff", "epic": "Customer Support",
        "subject": "Customer order history lookup (by mobile or order ID)",
        "story": "I want to look up any customer's order history and account details so I can resolve their support queries quickly.",
        "acceptance": "1. Search by mobile number or order ID.\n2. Full order history with statuses shown.\n3. Can view payment and refund status.\n4. Cannot edit payment data — view only.",
        "tech_notes": "MSSQL: read-only query; staff_id logged on every lookup (audit)",
        "mobile": "Search by mobile number is the primary lookup method",
        "priority": "High",
    },
    {
        "id": "STA-005", "sprint": None,
        "module": "Staff", "epic": "Customer Support",
        "subject": "Initiate refund or apply goodwill discount on behalf of customer",
        "story": "I want to initiate a refund or apply a goodwill discount on behalf of a customer to resolve a complaint quickly.",
        "acceptance": "1. Refund button on order detail (within policy rules).\n2. Reason mandatory; amount editable up to order value.\n3. Goodwill discount generates a one-time promo code.\n4. All actions logged with staff ID.",
        "tech_notes": "Razorpay Refund API; MSSQL: StaffActions audit table",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "STA-006", "sprint": None,
        "module": "Staff", "epic": "Vendor Support",
        "subject": "Edit or hide vendor product listings on their behalf",
        "story": "I want to help vendors with their product listings — editing or temporarily hiding items — when they contact support.",
        "acceptance": "1. Search vendor by name or mobile.\n2. Edit product title, price, stock on vendor's behalf.\n3. Hide/unhide listing without deleting.\n4. Vendor notified of changes via email.",
        "tech_notes": "MSSQL: Products; staff_id logged on update; Azure SendGrid to vendor",
        "mobile": "Vendor lookup by mobile number",
        "priority": "Normal",
    },
    {
        "id": "STA-007", "sprint": None,
        "module": "Staff", "epic": "KYC Verification",
        "subject": "In-browser KYC document review + approve/reject",
        "story": "I want to review KYC documents submitted by vendors and riders and approve or reject them, so only legitimate people operate on the platform.",
        "acceptance": "1. Document viewer in-browser (PDF + image).\n2. Approve / Reject with mandatory reason.\n3. Applicant notified via email + SMS.\n4. Approved vendors automatically get 'Active' status.",
        "tech_notes": "Azure Blob signed URL for doc preview; MSSQL: KYCReviews with reviewer_id",
        "mobile": "SMS to vendor/rider mobile on approval or rejection",
        "priority": "High",
    },
    {
        "id": "STA-008", "sprint": None,
        "module": "Staff", "epic": "Reports",
        "subject": "Daily operational shift report (PDF/Excel export)",
        "story": "I want to generate daily operational reports — orders processed, issues raised, refunds given — so I can share a shift summary with management.",
        "acceptance": "1. Date range selector.\n2. Metrics: orders handled, escalations, refunds issued, avg resolution time.\n3. Export as PDF or Excel.\n4. Filterable by staff member.",
        "tech_notes": "MSSQL aggregation; pdfkit for PDF; exceljs for XLSX",
        "mobile": "N/A",
        "priority": "Normal",
    },

    # ── RIDER ─────────────────────────────────────────────────────────────
    {
        "id": "RID-001", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Rider", "epic": "Onboarding & KYC",
        "subject": "Rider registration + DL/RC/Aadhaar upload",
        "story": "I want to register as a rider with my vehicle and documents so I can start earning on SpaceKart.",
        "acceptance": "1. Fields: name, mobile, vehicle type, number plate.\n2. Docs: DL, RC, Aadhaar (PDF/JPEG <=5MB).\n3. Reference ID issued immediately.\n4. KYC review within 24 hours.",
        "tech_notes": "Azure Blob for docs; MSSQL: Riders, RiderDocuments",
        "mobile": "Mobile verified via OTP at signup; primary contact for all ride alerts",
        "priority": "High",
    },
    {
        "id": "RID-002", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Rider", "epic": "Onboarding & KYC",
        "subject": "Rider bank account linking (micro-deposit verification)",
        "story": "I want to link my bank account so my earnings are automatically transferred to me after every payout cycle.",
        "acceptance": "1. IFSC + account number; micro-deposit verification.\n2. Encrypted at rest in MSSQL.\n3. Account editable after re-verification.",
        "tech_notes": "Razorpay Contact + Fund Account API; AES-256 for bank data at rest",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "RID-003", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Rider", "epic": "Ride Operations",
        "subject": "Online/offline availability toggle",
        "story": "I want to set myself as Online or Offline so I only receive delivery requests when I'm actually available to work.",
        "acceptance": "1. Toggle visible on home screen.\n2. Offline = no new requests.\n3. Active ride completes even if I go offline.\n4. Status visible to admin/staff.",
        "tech_notes": "MSSQL: Riders.is_available; real-time sync via Socket.io",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "RID-004", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Rider", "epic": "Ride Operations",
        "subject": "Delivery request with distance, area & payout preview",
        "story": "I want to receive delivery requests near me with the pickup address, drop address, and estimated payout so I can decide whether to accept.",
        "acceptance": "1. Request card shows: vendor name, customer area, distance, estimated payout.\n2. 60 seconds to accept or decline.\n3. Auto-declined if no response.\n4. Next nearest rider offered if declined.",
        "tech_notes": "Geo-query on MSSQL (lat/lng); Socket.io push to rider; fallback queue",
        "mobile": "Push notification to rider's mobile on new request",
        "priority": "High",
    },
    {
        "id": "RID-005", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Rider", "epic": "Ride Operations",
        "subject": "Turn-by-turn navigation to vendor then customer (Google Maps)",
        "story": "I want turn-by-turn navigation to the vendor (pickup) and then to the customer (drop) so I can complete deliveries efficiently.",
        "acceptance": "1. Google Maps Directions opens on accept.\n2. Pickup leg first; drop leg shown after pickup confirmed.\n3. ETA shown throughout.",
        "tech_notes": "Google Maps Directions API; deep-link to Google Maps app on mobile",
        "mobile": "Navigation opens in Google Maps native app via deep link",
        "priority": "High",
    },
    {
        "id": "RID-006", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Rider", "epic": "Ride Operations",
        "subject": "Live GPS location sharing (5-sec intervals, battery optimised)",
        "story": "I want my live location to be shared with the customer and vendor during an active delivery so everyone can track progress.",
        "acceptance": "1. GPS coordinates sent every 5 seconds when ride is active.\n2. Location sharing stops on ride completion.\n3. Battery optimisation: frequency reduces to 10s if speed < 5 km/h.",
        "tech_notes": "Socket.io + Azure SignalR; Node.js location update endpoint; MSSQL: RiderLocations",
        "mobile": "Background location permission required; prompt with explanation shown",
        "priority": "High",
    },
    {
        "id": "RID-007", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Rider", "epic": "Ride Operations",
        "subject": "Pickup & delivery confirmation (OTP or photo proof)",
        "story": "I want to confirm pickup at the vendor and delivery at the customer's door so the order status updates automatically.",
        "acceptance": "1. 'Confirm Pickup' button at vendor location.\n2. 'Confirm Delivery' requires OTP from customer (or photo proof if customer unavailable).\n3. Each confirmation triggers push to all parties.",
        "tech_notes": "MSSQL: OrderStatusHistory; FCM on each step",
        "mobile": "Customer delivery OTP sent to their registered mobile",
        "priority": "High",
    },
    {
        "id": "RID-008", "sprint": None,
        "module": "Rider", "epic": "Earnings",
        "subject": "Real-time earnings dashboard (today / week / month)",
        "story": "I want to see my earnings in real-time — today, this week, this month — so I can plan how much I need to work.",
        "acceptance": "1. Cards: Today, This week, This month earnings.\n2. Per-trip breakdown with order ID, distance, payout.\n3. Payout date shown.",
        "tech_notes": "MSSQL: RiderEarnings; aggregated with SUM per time-range",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "RID-009", "sprint": None,
        "module": "Rider", "epic": "Ratings",
        "subject": "Post-delivery rating for vendor and customer",
        "story": "I want to rate the vendor and customer after each delivery so the community maintains quality standards.",
        "acceptance": "1. Rating prompt shown after ride closed.\n2. 1-5 stars; optional comment.\n3. Ratings averaged and visible on profiles.\n4. Skippable after 3 seconds.",
        "tech_notes": "MSSQL: RiderRatings, CustomerRatings; avg computed via SQL view",
        "mobile": "N/A",
        "priority": "Normal",
    },

    # ── ADMIN ─────────────────────────────────────────────────────────────
    {
        "id": "ADM-001", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Admin", "epic": "User Management",
        "subject": "Admin universal user search (customer/vendor/staff/rider)",
        "story": "I want to search and view any customer, vendor, staff, or rider account so I can investigate issues and manage the platform.",
        "acceptance": "1. Search by name, mobile, email, or ID.\n2. Full profile view including KYC status.\n3. Account timeline: registrations, logins, orders.\n4. All admin views logged in audit trail.",
        "tech_notes": "MSSQL: unified Users view across roles; audit_log table",
        "mobile": "Search by mobile number supported for all roles",
        "priority": "High",
    },
    {
        "id": "ADM-002", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Admin", "epic": "User Management",
        "subject": "Account suspension & permanent ban with graceful handling",
        "story": "I want to suspend or permanently ban an account if there's a policy violation, so bad actors can't continue operating.",
        "acceptance": "1. Suspend: temporary with duration and reason.\n2. Ban: permanent; account access revoked immediately.\n3. In-progress rides/orders handled gracefully.\n4. User notified with reason.",
        "tech_notes": "MSSQL: Users.status enum; JWT blacklist via Redis on ban",
        "mobile": "SMS to user's mobile on suspension/ban",
        "priority": "High",
    },
    {
        "id": "ADM-003", "sprint": "Sprint 1 - Auth & Identity",
        "module": "Admin", "epic": "KYC Approval",
        "subject": "KYC review queue (vendor + rider, oldest-first, 1-click approve)",
        "story": "I want a KYC review queue where I can see all pending vendor and rider applications and approve or reject them quickly.",
        "acceptance": "1. Queue sorted by submission date (oldest first).\n2. Document preview in-browser without download.\n3. Approve one-click; Reject requires typed reason.\n4. Applicant notified instantly.",
        "tech_notes": "Azure Blob signed URLs for doc preview; MSSQL: KYCQueue; FCM + SMS on decision",
        "mobile": "SMS + push to applicant's registered mobile on decision",
        "priority": "High",
    },
    {
        "id": "ADM-004", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Admin", "epic": "Dispute Resolution",
        "subject": "Dispute queue with refund/reject/partial/escalate actions",
        "story": "I want to manage a dispute queue between buyers and vendors so I can investigate and resolve complaints fairly.",
        "acceptance": "1. Dispute card: order detail, both parties' accounts, chat history, photos.\n2. Actions: Approve Refund, Reject Claim, Partial Refund, Escalate.\n3. Resolution note sent to both parties.\n4. All actions logged with admin ID.",
        "tech_notes": "MSSQL: Disputes, DisputeMessages; Razorpay refund API on resolution",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "ADM-005", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Admin", "epic": "Platform Configuration",
        "subject": "Product category & sub-category management (drag-drop reorder)",
        "story": "I want to manage product categories and sub-categories so the catalog stays well-organised as the platform grows.",
        "acceptance": "1. Add/edit/delete categories.\n2. Drag-and-drop reorder.\n3. Deactivating a category hides its products from buyers.\n4. Vendor notified if their products are affected.",
        "tech_notes": "MSSQL: Categories with parent_id; cache invalidation on change",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "ADM-006", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Admin", "epic": "Platform Configuration",
        "subject": "Commission rate configuration (global + per-category, effective date)",
        "story": "I want to configure commission rates by category so I can control how the platform earns revenue.",
        "acceptance": "1. Global default + per-category override.\n2. New rate takes effect from a set date.\n3. Historical rates preserved for past payouts.\n4. Change logged with admin ID.",
        "tech_notes": "MSSQL: CommissionRates with effective_date; all payout calcs use rate at order time",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "ADM-007", "sprint": "Sprint 2 - Catalog & Discovery",
        "module": "Admin", "epic": "Platform Configuration",
        "subject": "Promo code creator + homepage banner scheduler",
        "story": "I want to create and manage promo codes and homepage banners so I can run campaigns that drive orders.",
        "acceptance": "1. Promo: type (% or flat), min order value, usage limit, expiry date.\n2. Banner: image upload, link URL, position, schedule dates.\n3. Both can be activated/deactivated instantly.",
        "tech_notes": "Azure Blob for banner images; MSSQL: PromoCodes, Banners; Redis for promo validation cache",
        "mobile": "N/A",
        "priority": "Normal",
    },
    {
        "id": "ADM-008", "sprint": "Sprint 3 - Orders & Payments",
        "module": "Admin", "epic": "Platform Monitoring",
        "subject": "Real-time ops dashboard (GMV, riders online, error rates)",
        "story": "I want a real-time operations dashboard showing live orders, active riders, GMV, and error rates so I can react fast if something goes wrong.",
        "acceptance": "1. Live counters: active orders, riders online, GMV today.\n2. Order funnel: Placed -> Confirmed -> Packed -> Delivered.\n3. API error rate gauge; alert if > 1%.\n4. Auto-refreshes every 30 seconds.",
        "tech_notes": "Azure Application Insights; Socket.io for live counters; Chart.js",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "ADM-009", "sprint": None,
        "module": "Admin", "epic": "Reports & Compliance",
        "subject": "Platform-wide revenue/order/payout reports (Excel + PDF export)",
        "story": "I want platform-wide revenue, order, and payout reports filterable by date, category, and region so I can make informed business decisions.",
        "acceptance": "1. GMV, net revenue, commissions, refunds breakdown.\n2. Filter by date range, category, vendor, city.\n3. Export to Excel and PDF.\n4. Scheduled email reports (daily/weekly).",
        "tech_notes": "MSSQL complex aggregations; exceljs + pdfkit; Azure Logic Apps for scheduling",
        "mobile": "N/A",
        "priority": "High",
    },
    {
        "id": "ADM-010", "sprint": None,
        "module": "Admin", "epic": "Reports & Compliance",
        "subject": "Full audit log (90-day retention, export for legal requests)",
        "story": "I want a full audit log of every sensitive action taken on the platform so we can meet compliance requirements and investigate incidents.",
        "acceptance": "1. Every login, data edit, admin action logged.\n2. Fields: user_id, role, action, entity_id, old_value, new_value, IP, timestamp.\n3. 90-day retention minimum.\n4. Export available for legal requests.",
        "tech_notes": "MSSQL: AuditLog (append-only); indexed on user_id + timestamp",
        "mobile": "N/A",
        "priority": "High",
    },
]

# Setup tasks for Sprint 0
SETUP_TASKS = [
    {
        "id": "SETUP-01", "sprint": "Sprint 0 - Foundation",
        "module": "Infrastructure",
        "subject": "[SETUP] Node.js API + MSSQL schema (all tables per Tech Notes)",
        "description": "Set up Node.js Express API project with MSSQL database. Create all tables as defined in the Tech Notes of each user story: Users, Vendors, Riders, Staff, Products, Orders, OrderItems, CartItems, Payments, Refunds, KYCDocuments, Addresses, CustomerAddresses, AuditLog, etc.",
        "priority": "High",
    },
    {
        "id": "SETUP-02", "sprint": "Sprint 0 - Foundation",
        "module": "Infrastructure",
        "subject": "[SETUP] Azure services bootstrap (Blob, SendGrid, FCM, Maps, SignalR)",
        "description": "Configure and test all Azure + external services:\n- Azure Blob Storage + CDN for images/documents\n- Azure SendGrid for transactional emails\n- Firebase Cloud Messaging (FCM) for push notifications\n- Azure Maps / Google Maps for geolocation\n- Azure SignalR for real-time Socket.io connections\n- Redis for caching and OTP storage",
        "priority": "High",
    },
    {
        "id": "SETUP-03", "sprint": "Sprint 0 - Foundation",
        "module": "Infrastructure",
        "subject": "[SETUP] Auth middleware (JWT + Redis OTP + Razorpay SDK)",
        "description": "Implement core authentication infrastructure:\n- JWT token issuer + refresh token rotation\n- Redis-backed OTP store with TTL\n- Twilio/MSG91 SMS integration for OTP delivery\n- Razorpay Node.js SDK setup and webhook configuration\n- RBAC middleware for role-based route protection",
        "priority": "High",
    },
    {
        "id": "SETUP-04", "sprint": "Sprint 0 - Foundation",
        "module": "Infrastructure",
        "subject": "[SETUP] CI/CD pipeline + staging environment",
        "description": "Set up CI/CD pipeline and staging environment:\n- GitHub Actions or Azure DevOps pipeline\n- Staging environment on Azure (separate from production)\n- Docker containerisation for all services\n- Environment variable management\n- Health check endpoints",
        "priority": "High",
    },
    {
        "id": "SETUP-05", "sprint": "Sprint 0 - Foundation",
        "module": "Infrastructure",
        "subject": "[SETUP] API contract (OpenAPI spec) + Postman collection",
        "description": "Document all API endpoints before implementation:\n- OpenAPI 3.0 specification for all endpoints\n- Postman collection with environment variables\n- Shared with frontend team for parallel development\n- Error response schemas documented\n- Authentication flows documented",
        "priority": "Normal",
    },
]

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def make_headers():
    if not TOKEN:
        print("ERROR: OPENPROJECT_TOKEN environment variable is not set.")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }

def api_get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", headers=make_headers(), params=params)
    if not r.ok:
        print(f"  GET {path} -> {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
    return r.json()

def api_post(path, data, retries=3):
    for attempt in range(1, retries + 1):
        r = requests.post(f"{BASE_URL}{path}", headers=make_headers(), json=data)
        if r.ok:
            return r.json()
        if r.status_code == 500 and attempt < retries:
            wait = attempt * 2
            print(f"  500 on attempt {attempt}, retrying in {wait}s...")
            time.sleep(wait)
            continue
        print(f"  POST {path} -> {r.status_code}: {r.text[:400]}")
        r.raise_for_status()
    return r.json()

def api_patch(path, data):
    r = requests.patch(f"{BASE_URL}{path}", headers=make_headers(), json=data)
    if not r.ok:
        print(f"  PATCH {path} -> {r.status_code}: {r.text[:400]}")
        r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def verify_auth():
    print("Verifying authentication...")
    me = api_get("/api/v3/users/me")
    print(f"  Authenticated as: {me.get('name', '?')} ({me.get('login', '?')})")
    return me

def get_or_create_project():
    print(f"\nLooking for project '{PROJECT_IDENTIFIER}'...")
    try:
        proj = api_get(f"/api/v3/projects/{PROJECT_IDENTIFIER}")
        print(f"  Found existing project: {proj['name']} (id={proj['id']})")
        return proj
    except requests.HTTPError as e:
        if e.response.status_code != 404:
            raise

    print("  Project not found. Creating...")
    proj = api_post("/api/v3/projects", {
        "name": "SpaceKart",
        "identifier": PROJECT_IDENTIFIER,
        "description": {
            "format": "markdown",
            "raw": (
                "## SpaceKart v0.0.1\n\n"
                "Hyperlocal e-commerce + delivery marketplace with AI voice assistant (Wicky).\n\n"
                "**Modules:** Customer · Vendor · Rider · Staff · Admin · AI Wicky\n\n"
                "**Timeline:** 90 days (May 21 – Aug 19, 2026) | 60% dev + 40% testing\n\n"
                "**Client:** SpaceKart | **Managed by:** MySillyDreams"
            ),
        },
        "public": False,
    })
    print(f"  Created project: {proj['name']} (id={proj['id']})")
    return proj

def get_type_id(project_id):
    print("\nLooking up 'User Story' work package type...")
    resp = api_get(f"/api/v3/projects/{project_id}/types")
    types = resp.get("_embedded", {}).get("elements", [])
    for t in types:
        if t["name"].lower() in ("user story", "story", "feature"):
            print(f"  Found type: '{t['name']}' (id={t['id']})")
            return t["id"], t["name"]
    names = [t["name"] for t in types]
    print(f"  WARNING: 'User Story' type not found in project. Available: {names}")
    print("  Falling back to first available type...")
    if types:
        print(f"  Using: '{types[0]['name']}' (id={types[0]['id']})")
        return types[0]["id"], types[0]["name"]
    raise RuntimeError("No work package types found in project!")

def get_task_type_id(project_id):
    resp = api_get(f"/api/v3/projects/{project_id}/types")
    types = resp.get("_embedded", {}).get("elements", [])
    for t in types:
        if t["name"].lower() in ("task", "infrastructure task"):
            return t["id"]
    return types[0]["id"] if types else None

def get_priority_map():
    print("\nLooking up priorities...")
    resp = api_get("/api/v3/priorities")
    priorities = resp.get("_embedded", {}).get("elements", [])
    pmap = {}
    for p in priorities:
        href = p["_links"]["self"]["href"]
        pmap[p["name"].lower()] = href
        print(f"  Priority: '{p['name']}' -> {href}")
    # Build convenience lookups
    result = {
        "High":   pmap.get("high")   or pmap.get("urgent") or list(pmap.values())[0],
        "Normal": pmap.get("normal") or pmap.get("medium") or list(pmap.values())[0],
        "Low":    pmap.get("low")    or pmap.get("minor")  or list(pmap.values())[-1],
    }
    print(f"  Mapped -> High={result['High']}, Normal={result['Normal']}, Low={result['Low']}")
    return result

def get_existing_subjects(project_id):
    print("\nFetching existing work packages (idempotency check)...")
    resp = api_get(f"/api/v3/projects/{project_id}/work_packages", params={"pageSize": 500})
    wps = resp.get("_embedded", {}).get("elements", [])
    subjects = {wp["subject"] for wp in wps}
    print(f"  Found {len(subjects)} existing work packages to skip duplicates.")
    return subjects

def get_sprint_map(project_id):
    print(f"\nFetching sprints for project {project_id}...")
    try:
        resp = api_get(f"/api/v3/projects/{project_id}/sprints")
        sprints = resp.get("_embedded", {}).get("elements", [])
        if not sprints:
            return {}
        smap = {}
        for s in sprints:
            smap[s["name"]] = s["_links"]["self"]["href"]
            print(f"  Sprint: '{s['name']}' -> {s['_links']['self']['href']}")
        return smap
    except Exception as e:
        print(f"  Could not fetch sprints: {e}")
        return {}

def build_wp_body(story, project_id, type_href, priority_href, sprint_href):
    desc_md = (
        f"**Original ID:** {story['id']}\n\n"
        f"**Epic / Feature Area:** {story['epic']}\n\n"
        f"**Module:** {story['module']}\n\n"
        f"---\n\n"
        f"**User Story:**\n{story['story']}\n\n"
        f"---\n\n"
        f"**Acceptance Criteria:**\n{story['acceptance']}\n\n"
        f"**Tech Notes:** {story['tech_notes']}\n\n"
        f"**Mobile Validation:** {story.get('mobile', 'N/A')}"
    )
    body = {
        "subject": f"[{story['id']}] {story['subject']}",
        "description": {"format": "markdown", "raw": desc_md},
        "_links": {
            "project":  {"href": f"/api/v3/projects/{project_id}"},
            "type":     {"href": type_href},
            "priority": {"href": priority_href},
        },
    }
    if sprint_href:
        body["_links"]["sprint"] = {"href": sprint_href}
    return body

def build_setup_task_body(task, project_id, type_href, priority_href, sprint_href):
    body = {
        "subject": task["subject"],
        "description": {"format": "markdown", "raw": task["description"]},
        "_links": {
            "project":  {"href": f"/api/v3/projects/{project_id}"},
            "type":     {"href": type_href},
            "priority": {"href": priority_href},
        },
    }
    if sprint_href:
        body["_links"]["sprint"] = {"href": sprint_href}
    return body

# ---------------------------------------------------------------------------
# Main phases
# ---------------------------------------------------------------------------

def phase_create_project():
    verify_auth()
    proj = get_or_create_project()
    print("\n" + "="*60)
    print("PROJECT CREATED SUCCESSFULLY")
    print("="*60)
    print(f"\n  URL: {BASE_URL}/projects/{PROJECT_IDENTIFIER}")
    print(f"  ID:  {proj['id']}")
    print()
    print("NEXT STEPS — complete these manually in the browser:")
    print("-"*60)
    print(f"  1. Open: {BASE_URL}/projects/{PROJECT_IDENTIFIER}/settings/modules")
    print("     Enable the 'Backlogs' module, then Save.")
    print()
    print(f"  2. Open: {BASE_URL}/projects/{PROJECT_IDENTIFIER}/backlogs/backlog")
    print("     Click '+ Sprint' and create these 6 sprints (in order):")
    print()
    sprint_table = [
        ("Sprint 0 - Foundation",              "2026-05-21", "2026-06-03"),
        ("Sprint 1 - Auth & Identity",         "2026-06-04", "2026-06-17"),
        ("Sprint 2 - Catalog & Discovery",     "2026-06-18", "2026-07-01"),
        ("Sprint 3 - Orders & Payments",       "2026-07-02", "2026-07-14"),
        ("Test Sprint 1 - Integration",        "2026-07-15", "2026-07-28"),
        ("Test Sprint 2 - E2E & Performance",  "2026-07-29", "2026-08-11"),
    ]
    for name, start, end in sprint_table:
        print(f"     Name: {name}")
        print(f"     Start: {start}   Finish: {end}")
        print()
    print("  3. Once sprints are created, run:")
    print("     python setup_spacekart_project.py --stories")
    print("="*60)


def phase_create_stories():
    verify_auth()

    proj = get_or_create_project()
    project_id = proj["id"]

    type_id, type_name = get_type_id(project_id)
    task_type_id = get_task_type_id(project_id)
    type_href = f"/api/v3/types/{type_id}"
    task_type_href = f"/api/v3/types/{task_type_id}"

    pmap = get_priority_map()
    sprint_map = get_sprint_map(project_id)
    existing_subjects = get_existing_subjects(project_id)

    missing_sprints = [n for n in SPRINT_NAMES if n not in sprint_map]
    if missing_sprints:
        print("\nWARNING: The following sprints were not found:")
        for s in missing_sprints:
            print(f"  - '{s}'")
        print("\nStories assigned to missing sprints will be created in the Product Backlog.")
        print("(Sprint name must match EXACTLY — check for typos in the web UI)")

    total = len(SETUP_TASKS) + len(STORIES)
    created = 0
    errors = []

    print(f"\nCreating {len(SETUP_TASKS)} setup tasks + {len(STORIES)} user stories ({total} total)...")
    print("-" * 60)

    # Setup tasks
    for task in SETUP_TASKS:
        if task["subject"] in existing_subjects:
            print(f"  SKIP (exists): {task['id']}")
            continue
        sprint_href = sprint_map.get(task["sprint"])
        priority_href = pmap[task["priority"]]
        body = build_setup_task_body(task, project_id, task_type_href, priority_href, sprint_href)
        try:
            wp = api_post("/api/v3/work_packages", body)
            created += 1
            sprint_label = task["sprint"] if sprint_href else "Product Backlog"
            print(f"  [{created}/{total}] {task['id']} -> WP #{wp.get('id')} [{sprint_label}]")
        except Exception as e:
            errors.append((task["id"], str(e)))
            print(f"  FAILED: {task['id']} - {e}")
        time.sleep(0.3)

    # User stories
    for story in STORIES:
        subject = f"[{story['id']}] {story['subject']}"
        if subject in existing_subjects:
            print(f"  SKIP (exists): {story['id']}")
            continue
        sprint_href = sprint_map.get(story["sprint"]) if story["sprint"] else None
        priority_href = pmap[story["priority"]]
        body = build_wp_body(story, project_id, type_href, priority_href, sprint_href)
        try:
            wp = api_post("/api/v3/work_packages", body)
            created += 1
            sprint_label = story["sprint"] if sprint_href else ("Product Backlog" if not story["sprint"] else f"MISSING: {story['sprint']}")
            print(f"  [{created}/{total}] {story['id']} -> WP #{wp.get('id')} [{sprint_label}]")
        except Exception as e:
            errors.append((story["id"], str(e)))
            print(f"  FAILED: {story['id']} - {e}")
        time.sleep(0.3)

    print("\n" + "="*60)
    print(f"DONE: {created}/{total} work packages created")
    if errors:
        print(f"\nFAILED ({len(errors)}):")
        for eid, err in errors:
            print(f"  {eid}: {err}")
    else:
        print("All work packages created successfully!")
    print("="*60)
    print(f"\nView project: {BASE_URL}/projects/{PROJECT_IDENTIFIER}/backlogs/backlog")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SpaceKart OpenProject Scrum Setup")
    parser.add_argument("--stories", action="store_true",
                        help="Create all 75 user stories (run after creating sprints manually)")
    args = parser.parse_args()

    if args.stories:
        phase_create_stories()
    else:
        phase_create_project()
