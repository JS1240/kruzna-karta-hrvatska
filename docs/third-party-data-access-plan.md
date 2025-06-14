# Third-Party Data Access Plan

This document outlines a proposal for exposing curated event data and analytics to external partners through a paid API and data export service.

## Goals

1. Provide a secure interface for travel agencies, marketing firms and other partners to integrate event listings and aggregated statistics.
2. Offer granular access controls and usage limits tied to subscription plans.
3. Reuse existing FastAPI infrastructure with minimal disruption to the main platform.

## Key Features

### 1. API Authentication
- Partners receive an API key after subscribing.
- Keys are validated via the `X-API-Key` header on each request.
- API keys can be revoked or rotated from the admin dashboard.

### 2. Event Data Endpoints
- `GET /api/third-party/events` – returns upcoming events with optional date range filters.
- `GET /api/third-party/events/{id}` – fetch a single event with translated fields.
- Pagination and basic filtering (category, city, etc.) mirror the public `/events` API.

### 3. Analytics Reports
- `GET /api/third-party/analytics/summary` – aggregated platform metrics over a specified period.
- `GET /api/third-party/analytics/popular-events` – top events by view count.
- Response shapes match the internal analytics routes but exclude personal data.

### 4. Data Export
- Partners can request CSV exports via `GET /api/third-party/export/events.csv`.
- Exports are generated on demand and cached for short periods.

### 5. Rate Limiting & Billing
- Each API key has a monthly request quota.
- Usage is tracked in the database and surfaced in the admin panel.
- Exceeding the quota returns HTTP `429 Too Many Requests`.

## Implementation Steps

1. Add `THIRD_PARTY_API_KEYS` to `.env` and `Settings`.
2. Create `ThirdPartyAuth` dependency to validate the API key.
3. Implement new FastAPI router `third_party.py` with read‑only endpoints for events and analytics.
4. Register the router in `app.main` under the `/api` prefix.
5. Document sample requests and response formats.

## Future Ideas

- OAuth application registration for partners instead of static keys.
- Webhooks for real‑time event updates.
- Dashboard where partners can monitor their usage statistics.

