# AGENTS.md

## Project Overview

This project is a B2B software platform for Ethiopia's pharmaceutical supply chain. It is a marketplace that connects licensed pharmaceutical importers with pharmacies that need reliable access to medicines, medical supplies, and related healthcare products.

The platform should reduce friction in pharmaceutical procurement by helping verified pharmacies discover available products, compare importer offerings, place orders, manage purchasing workflows, and maintain better visibility into supply availability. For importers, the platform should provide a trusted digital sales channel for listing products, managing inventory, receiving qualified demand, and growing pharmacy relationships.

The product must account for the realities of the Ethiopian pharmaceutical market, including regulated medicine distribution, importer licensing, pharmacy verification, variable product availability, payment and logistics constraints, and the importance of trust between buyers and sellers.

## Product Vision

Build the trusted digital marketplace for pharmaceutical trade in Ethiopia.

The platform should become the default procurement and sales infrastructure for verified pharmacies and licensed pharmaceutical importers. It should make medicine sourcing more transparent, efficient, and dependable while supporting regulatory compliance and responsible distribution.

The long-term vision is to:

- Improve access to legitimate pharmaceutical products across Ethiopia.
- Help pharmacies source medicines faster and with more confidence.
- Give importers a scalable digital channel for product discovery, order management, and customer retention.
- Reduce informal, opaque, and inefficient procurement practices.
- Support better stock visibility across the pharmaceutical supply chain.
- Enable subscription-based business tools for importers and pharmacy buyers.
- Create a compliance-aware marketplace where only verified businesses can transact.

The platform should feel practical, trustworthy, and operations-focused. It is not a consumer shopping app. It is a professional procurement tool for businesses handling regulated healthcare products.

## Core User Personas

### Importer

An Importer is a licensed pharmaceutical importer or distributor operating in Ethiopia. They use the platform to sell products to verified pharmacies and manage commercial relationships at scale.

Primary goals:

- Reach more verified pharmacy buyers.
- List available pharmaceutical products and medical supplies.
- Communicate stock availability, pricing, minimum order quantities, and expiry details.
- Receive qualified inquiries and orders from legitimate pharmacy businesses.
- Manage inventory visibility and reduce manual sales coordination.
- Build trust through verified business credentials.
- Access analytics on demand, product performance, and buyer behavior.

Common pain points:

- Sales are often handled manually by phone, messaging apps, or field agents.
- Product availability changes frequently and is difficult to broadcast accurately.
- Buyers may request products without clear business verification.
- Managing price lists, stock updates, and customer communications is time-consuming.
- There is limited visibility into demand trends across pharmacy buyers.

Important product needs:

- Business verification and license management.
- Product catalog tools.
- Inventory and stock status management.
- Order and inquiry management.
- Buyer relationship management.
- Subscription plans for marketplace visibility and advanced tools.
- Reporting and analytics.

### Pharmacy Buyer

A Pharmacy Buyer is a licensed pharmacy owner, manager, or procurement staff member responsible for sourcing pharmaceutical products for resale or dispensing.

Primary goals:

- Find legitimate importers with available stock.
- Search and compare products, prices, pack sizes, minimum order quantities, and expiry dates.
- Place orders or send purchase inquiries efficiently.
- Track procurement history and supplier relationships.
- Reduce time spent calling multiple importers to check stock.
- Gain confidence that suppliers are verified and products are legitimate.

Common pain points:

- It can be difficult to know which importer has stock for a needed product.
- Price, availability, and expiry information may not be current.
- Procurement is fragmented across calls, visits, messaging apps, and paper records.
- Smaller pharmacies may have less access to importer networks.
- Trust and product authenticity are critical concerns.

Important product needs:

- Pharmacy business verification.
- Searchable product catalog.
- Supplier comparison.
- Order, quote, or inquiry workflows.
- Saved suppliers and favorite products.
- Purchase history.
- Alerts for restocked or high-demand products.
- Subscription options for advanced procurement tools.

## Key Features

### User Verification and KYC

- Business registration and license verification for importers.
- Pharmacy license verification for pharmacy buyers.
- Admin review and approval workflows.
- Document upload for licenses, tax records, and business credentials.
- User roles and permissions for teams within importer and pharmacy accounts.
- Verification status badges visible in the marketplace.
- Periodic re-verification for expired licenses or documents.

### Product Catalog

- Importer-managed product listings.
- Product details such as brand name, generic name, strength, dosage form, pack size, manufacturer, country of origin, and regulatory information.
- Product categorization by therapeutic area, dosage form, or supply type.
- Search and filtering for pharmacy buyers.
- Product images and supporting documentation where appropriate.
- Pricing visibility based on account type, verification status, or subscription tier.
- Minimum order quantities and bulk pricing support.

### Inventory Management

- Stock availability updates for importers.
- Inventory status indicators such as in stock, low stock, out of stock, and available soon.
- Batch, expiry date, and quantity visibility where operationally appropriate.
- Import tools for bulk product and inventory updates.
- Alerts for low stock, expiring stock, or restocked items.
- Pharmacy buyer notifications for watched products.

### Ordering and Procurement

- Pharmacy-to-importer order requests.
- Quote request and negotiation workflow.
- Order status tracking from submitted to confirmed, fulfilled, cancelled, or rejected.
- Purchase history for pharmacy buyers.
- Sales history for importers.
- Messaging or structured inquiry threads tied to products and orders.
- Support for offline payment and delivery coordination where needed.

### Subscriptions and Monetization

- Subscription plans for importers based on catalog size, visibility, analytics, or lead volume.
- Subscription plans for pharmacy buyers based on procurement tools, alerts, saved searches, or advanced supplier access.
- Free or trial tiers for onboarding new businesses.
- Billing history and subscription management.
- Feature gating based on subscription tier.
- Admin controls for plan management, discounts, and manual overrides.

### Trust, Safety, and Compliance

- Verified-only marketplace access for regulated transactions.
- Admin moderation of users, documents, products, and reported issues.
- Audit logs for key account, product, inventory, and order changes.
- Clear separation between verified businesses and pending applicants.
- Compliance-aware product listing rules.
- Reporting tools for suspicious users, products, or transactions.

### Admin Operations

- Admin dashboard for reviewing KYC submissions.
- User and company management.
- Product and listing moderation.
- Subscription and billing oversight.
- Marketplace analytics.
- Support ticket or issue management.
- Manual account verification, suspension, and reactivation.

### Analytics and Reporting

- Importer analytics for product views, inquiries, orders, and buyer interest.
- Pharmacy buyer reports for purchasing activity and supplier usage.
- Marketplace-level analytics for admins.
- Demand trend reporting by product category, region, or time period.
- Exportable reports for operational review.

## Product Principles

- Trust first: only verified businesses should be able to participate in meaningful marketplace activity.
- Compliance-aware by default: pharmaceutical distribution is regulated, and product workflows should reflect that.
- Operational clarity over visual novelty: users need fast, reliable workflows more than decorative interfaces.
- Mobile-friendly but business-grade: many users may operate from phones, but the experience should still support serious procurement work.
- Current inventory matters: stale availability data undermines trust, so inventory update workflows must be simple.
- Support real-world workflows: payment, delivery, and negotiation may happen offline at first, and the software should still help organize the process.

## Engineering Notes for Future Agents

- Preserve the B2B marketplace framing. Do not treat this as a consumer ecommerce app.
- Model Importer and Pharmacy Buyer as distinct business account types with different permissions and workflows.
- Keep verification status central to access control and marketplace trust.
- Prefer explicit order, quote, inventory, and subscription states over loosely typed status strings.
- Design features with Ethiopian pharmaceutical business operations in mind.
- Avoid adding regulated medical claims or patient-facing medication advice unless explicitly required and legally reviewed.

