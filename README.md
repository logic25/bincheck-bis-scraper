# bincheck-bis-scraper

Standalone Playwright microservice that scrapes live BIS (Building Information System) data from the NYC DOB website. Used by BinCheck's edge functions to fetch real-time job filing data that predates or differs from the stale Socrata dataset (`scjx-j6np`).

> **Note:** This service is called via the `bis-scraper-proxy` Supabase edge function — it is never called directly from the frontend.

---

## Deploy: Railway (one-click from repo)

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Railway detects the `Procfile` automatically — no extra config needed
3. Set the environment variables below
4. Railway assigns a public URL (e.g. `https://bincheck-bis-scraper-production.up.railway.app`)
5. Copy that URL into your Supabase `BIS_SCRAPER_URL` secret

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SCRAPER_SECRET` | Yes | Shared secret for `X-Scraper-Secret` header auth. Generate with `openssl rand -hex 16` (32 hex chars). Must match `BIS_SCRAPER_SECRET` in Supabase. |
| `PORT` | Auto | Set automatically by Railway. Do not set manually. |

---

## Endpoints

### `GET /health`

Returns service status. No auth required.

```json
{
  "status": "ok",
  "service": "bincheck-bis-scraper",
  "secret_configured": true
}
```

### `POST /api/scrape`

Requires `X-Scraper-Secret: <SCRAPER_SECRET>` header.

**Request body:**

```json
{
  "action": "jobs",
  "bin": "1234567"
}
```

**Response:** JSON object (shape depends on action — see below).

---

## Actions

### `profile` — Property Profile

Fetches vacate orders, restriction flags, and aggregate counts from the BIS Property Profile Overview page.

**Request:**
```json
{ "action": "profile", "bin": "1234567" }
```

**Response:**
```json
{
  "bin": "1234567",
  "vacate_order": false,
  "vacate_type": null,
  "counts": {
    "complaints_total": 12,
    "complaints_open": 2,
    "violations_dob_total": 5,
    "violations_dob_open": 1,
    "violations_ecb_total": 3,
    "violations_ecb_open": 0,
    "jobs_total": 42,
    "actions_total": 8
  },
  "restrictions": {
    "landmark_status": null,
    "sro_restricted": "NO",
    ...
  },
  "cross_streets": "MAIN ST / BROADWAY",
  "scraped_at": "2024-01-15T10:30:00.000000"
}
```

---

### `jobs` — Jobs/Filings by BIN

Fetches all job filings for a BIN from the BIS Jobs by Location page, including PAA (Prior Action Applications).

**Request:**
```json
{ "action": "jobs", "bin": "1234567" }
```

**Response:**
```json
{
  "bin": "1234567",
  "jobs": [
    {
      "filing_date": "01/15/2024",
      "job_number": "123456789",
      "doc_number": "01",
      "job_type": "Alteration Type 1",
      "job_type_code": "A1",
      "job_status": "APPROVED",
      "job_status_code": "APPROVED",
      "status_date": "03/20/2024",
      "license_number": "0034627",
      "license_type": "PE",
      "applicant": "JOHN DOE",
      "zoning_approval": "NOT APPLICABLE",
      "description": "GENERAL CONSTRUCTION Work on Floor(s): 3",
      "floors": "3",
      "withdrawn": false,
      "source": "BIS_SCRAPE"
    }
  ],
  "job_count": 1,
  "scraped_at": "2024-01-15T10:30:00.000000"
}
```

---

### `job_detail` — Single Job Detail

Returns all filing documents for a specific job number. Provide `bin` for reliable results (avoids Akamai block on the direct job URL).

**Request:**
```json
{ "action": "job_detail", "job_number": "123456789", "bin": "1234567" }
```

**Response:**
```json
{
  "job_number": "123456789",
  "documents": [ ...same shape as jobs array above... ],
  "doc_count": 3,
  "withdrawn": false,
  "scraped_at": "2024-01-15T10:30:00.000000"
}
```

---

## Architecture

```
Frontend (BinCheck)
    └── Supabase Edge: bis-scraper-proxy
            └── Railway: bincheck-bis-scraper  ←── this repo
                    └── Playwright → a810-bisweb.nyc.gov (BIS)
```

The proxy layer keeps `BIS_SCRAPER_URL` and `BIS_SCRAPER_SECRET` out of the frontend bundle.

---

## Local Development

```bash
pip install -r requirements.txt
playwright install chromium
SCRAPER_SECRET=dev-secret python server.py
# → http://localhost:8080/health
```
