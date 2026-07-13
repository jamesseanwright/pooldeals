# PoolDeals Product Context & MVP Specifications---### Core Mission & Strategic Focus

PoolDeals is a hyper-local B2C discount and voucher platform designed for **Blackpool, UK**.

```
[Local Businesses] ---> Seasonal Deals / Vouchers ---> [Verified Blackpool Residents]
(Merchant Dashboard) (Consumer App)
```

#### The Core Problem

Blackpool’s economy heavily depends on seasonal tourism. Local businesses experience severe revenue drops during the off-season months.

#### The Solution

PoolDeals stabilizes local merchant revenue by incentivising year-round spending from permanent Blackpool residents.

#### Guardrails

- **Exclusivity:** Only verified local residents can access and redeem offers.
- **MVP Scope:** Keep functionality minimal, reliable, and highly scannable.

---

### 1. Consumer Platform (Local Residents)

#### Core Objective

Allow verified Blackpool residents to easily discover, secure, and redeem local business promotions.

#### Key Features & Flow

- **Geofenced Registration:** Users sign up via postcode verification (e.g., FY1 through FY8).
- **Deal Discovery Feed:** A simple list view searchable by category (Food, Retail, Leisure).
- **Voucher Claiming:** One-click action to generate a unique digital voucher code.
- **Offline Redemption:** Presenting a QR code or alphanumeric string at the physical point of sale.

#### MVP Acceptance Criteria

- System must restrict registration to valid Blackpool area postcodes.
- The discovery feed must load active promotions in under two seconds.
- Users can claim a maximum of 3 active vouchers simultaneously to prevent hoarding.
- Vouchers must feature clear, unalterable expiration dates.

---

### 2. Merchant Platform (Local Businesses)

#### Core Objective

Enable Blackpool business owners to launch, manage, and track hyper-local discount campaigns with zero technical overhead.

#### Key Features & Flow

- **Self-Serve Campaign Builder:** A single-page form to launch a new voucher.
- **Basic Analytics:** Simple metrics tracking vouchers issued versus vouchers redeemed.
- **Voucher Validator:** A lightweight mobile web interface to scan or type in consumer codes.

#### Campaign Creation Parameters

- **Title:** (e.g., "50% Off Winter Menu")
- **Discount Type:** Percentage, fixed amount, or Buy-One-Get-One (BOGO).
- **Total Inventory Caps:** Maximum number of vouchers available for distribution.
- **Validity Window:** Specific start and end dates to target off-peak weeks.

#### MVP Acceptance Criteria

- Merchants can launch a campaign in under five steps.
- Campaign metrics must update within 15 minutes of a consumer redemption.
- Merchants must have the ability to manually pause a campaign instantly.

---

### 3. Core MVP Data Schema (Simplified)

```
[Merchant] 1 ---- _ [Campaign] 1 ---- _ [Voucher] \* ---- 1 [Consumer]
```

- **Merchant Profile:** Name, category, Blackpool business address, verified status.
- **Campaign Entity:** ID, merchant ID, title, discount type, total supply, remaining supply, expiry.
- **Voucher Entity:** Unique code, campaign ID, consumer ID, status (Claimed, Redeemed, Expired).
- **Consumer Profile:** Name, email, verified Blackpool postcode, active claims count.
