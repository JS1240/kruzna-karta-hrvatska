# Premium Event Analytics Plan

This document proposes a high level plan for enabling paid users to access advanced analytics and organisational tools for managing events.

## Goals

1. Offer actionable insights for event organisers.
2. Provide revenue-generating features available only to paying subscribers.
3. Integrate with the existing FastAPI and React codebase with minimal disruption.

## Key Features

### 1. Advanced Dashboard
- **Revenue Trends**: Show charts of ticket sales, total revenue, organiser earnings and platform fees over custom date ranges.
- **Engagement Metrics**: Display page views, search analytics and user interactions for each event.
- **Conversion Analytics**: Track views-to-bookings ratios and highlight high performing events.
- **Geographic Breakdown**: Summarise revenue and bookings by location using Mapbox visualisations.

### 2. Event Organisation Tools
- **Schedule Planner**: Calendar view of all upcoming events with drag-and-drop rescheduling.
- **Task Checklist**: Custom tasks per event (marketing, logistics, staff) with progress tracking.
- **Performance Alerts**: Notify organisers when ticket sales or engagement drop below expected thresholds.

### 3. Access Control
- **Subscription Tiers**: Use Stripe to manage paid plans (e.g. Basic vs. Pro). Only paying users can access the advanced dashboard and organiser tools.
- **Role Permissions**: Extend the existing role system to include `analytics_viewer` or `organiser_pro` roles. Middleware checks the user’s subscription status before returning analytics data.

## Implementation Steps

1. **Database Extensions**
   - Add tables for subscription plans and user subscriptions.
   - Record event tasks and schedule items for the planner.
2. **Backend APIs**
   - Extend the `/analytics` routes to provide detailed metrics aggregated by day, week and month.
   - Create endpoints for organiser task lists and schedule entries.
   - Add middleware in FastAPI to verify the user has an active paid subscription before accessing premium endpoints.
3. **Frontend Updates**
   - Implement a new `PremiumDashboard` React page that consumes the enhanced analytics APIs.
   - Add subscription management pages (upgrade, billing history) using Stripe’s client library.
   - Integrate calendar and task components for event organisation.
4. **Payment Integration**
   - Use `StripeService` to create checkout sessions and listen for `invoice.paid` webhooks to activate the subscription.
   - Store subscription status and plan type in the user profile.
5. **Deployment and Testing**
   - Add feature flags in `.env` to toggle premium analytics.
   - Write end-to-end tests to ensure only paying users can access the premium routes and UI.

## Future Ideas

- Export analytics reports as CSV or PDF.
- Provide API access for organisers to integrate analytics into external tools.
- Offer white-label branding for venues on the Pro plan.

