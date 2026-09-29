my_motii — Implementation Plan
Version: 1.0
Status: Approved for execution
Owner: Founder / CTO
Last updated: 2026-09-21

Table of contents
Executive summary

Product vision and scope

Strategic sequencing

Architecture principles (contract)

Delivery phases

Phase details (workstreams, deliverables, exit criteria)

Team structure and responsibilities

Engineering standards

Data, compliance, and legal

Monetization and pricing

Go-to-market

Risk register

Success metrics

Governance and decision log

Appendices

1. Executive summary
What we are building. A multi-tenant vertical SaaS that becomes the operating system for the Kenyan auto-parts trade. Retailers run their entire shop on it (inventory, POS, receipts, KRA/eTIMS, expenses, profit). Suppliers get a controlled distribution and order channel into those shops. Eventually, garages, mechanics, and financing partners plug into the same network.

The strategic wedge. Own the retailer's daily workflow first. Once thousands of retailers run stock, sales, and purchasing through my_motii, the supplier network becomes the highest-value asset in the chain — and the second revenue engine.

Why now.

Kenyan auto-parts trade is digitizing fast but remains fragmented.

KRA eTIMS mandates force every shop to adopt compliant software.

M-Pesa ubiquity makes digital payments the default.

Existing POS solutions are generic; none understand vehicle fitment, OEM cross-reference, or the retailer↔supplier workflow.

What success looks like.

Year 1: 500 paying retailers, 40 active suppliers, KES 12M ARR.

Year 2: 3,000 retailers, 250 suppliers, KES 90M ARR, marketplace commission revenue stream live.

Year 3: The dominant vertical OS in the region; financing and data products contributing 20%+ of revenue.

Total build horizon: 18 months to full platform, delivered in five phases.

Team requirement: 1 founder/CTO, 1 tech lead, 3 backend, 2 frontend, 1 mobile/desktop, 1 QA, 1 designer, 1 DevOps/SRE, 1 support lead. Roughly 12 people at peak.

2. Product vision and scope
2.1 Vision statement
To be the operating system that connects auto-parts shops, garages, distributors, and manufacturers across East Africa — from the moment a customer asks for a part, to the moment it is delivered, installed, and paid for.

2.2 Product pillars
Pillar	What it does	Primary user
Retailer OS	Inventory, POS, documents, accounting, eTIMS, offline POS	Shop owner, cashier, manager
Supplier Console	Catalog distribution, pricing, orders, RFQs, retailer network	Wholesaler, distributor, importer
Network	Retailer↔supplier relationships, marketplace, RFQ, delivery	Both
Intelligence	Demand analytics, forecasting, reorder automation	Owner, supplier, platform
Ecosystem	Garages, mechanics, job cards, financing partners	Garage, mechanic, lender
2.3 In scope for v1 (phases 1–2)
Multi-tenant retailer tenant with branches

Product catalog + vehicle fitment + OEM cross-reference

Inventory with append-only stock ledger

POS with offline capability, thermal receipt printing

Customers (walk-in, garage, fleet, credit)

Suppliers and purchase orders

Expenses, income, basic P&L

KRA eTIMS integration

M-Pesa Daraja integration

SMS/WhatsApp notifications

Offline sync engine

Subscription billing

2.4 Explicitly out of scope for v1
Native iOS/Android consumer app

Financing (as principal)

Insurance products

Full accounting (double-entry GL — later phase)

Manufacturing / BOM

Cross-border (Uganda, Tanzania, Rwanda) — post Year 1

AI forecasting (post Year 1)

2.5 Non-goals
Becoming an accounting firm

Becoming a lender (partner, never principal)

Becoming a logistics company (integrate, don't own)

Competing with Jumia / generic e-commerce

3. Strategic sequencing
The order matters more than the features.

text
Retailer utility  →  Purchasing ease  →  Network effects  →  Ecosystem  →  Intelligence
   (Phase 1)          (Phase 2)            (Phase 3)         (Phase 4)      (Phase 5)
We do not build the marketplace first. We do not build the supplier portal first. We build the boring, daily-use retailer software that a shop cannot run without — then connect it to the supply side once retailer density is real.

Rationale:

Retailer pain is immediate and daily (stock, sales, receipts, KRA).

Supplier pain is periodic (orders, catalog, receivables) and only solvable at scale.

Network value compounds with retailer density. Doing it in reverse is how vertical marketplaces die.

4. Architecture principles (contract)
These are non-negotiable. Any deviation requires an ADR.

#	Principle	Consequence
1	Retailer tenant is the center of the data model	Supplier network is an integration layer, not the core
2	Multi-tenancy from day one	Every tenant-owned row carries tenant_id; PostgreSQL RLS enforces isolation
3	Stock is an append-only ledger	Never mutate quantity; every change is a movement event
4	Documents are numbered, gapless, and immutable	Void/reverse, never delete
5	Offline-first for POS	Local DB + outbox queue + idempotent sync
6	Django is the domain spine; FastAPI is the edge	FastAPI orchestrates HTTP; all business logic lives in shared/ or Django services
7	eTIMS, M-Pesa, WhatsApp are isolated modules	Vendors change; domain does not depend on them
8	Platform-owned vs tenant-owned data is explicit	Vehicle DB is platform; stock is tenant; never mix
9	nginx is the only reverse proxy	TLS terminates at edge; WebSockets route directly to FastAPI
10	Every action is auditable	WHO, WHAT, WHEN, WHERE, BEFORE, AFTER, DEVICE
11	Correlation ID flows end-to-end	HTTP → FastAPI → Django → Celery → external APIs
12	Cache keys are tenant-namespaced	Cross-tenant leakage is unacceptable
13	Money is integer minor units	No floats. Ever.
14	Time is UTC in DB, Africa/Nairobi at edge	One rule, everywhere
5. Delivery phases
Phase	Name	Duration	Outcome
0	Foundation	3 weeks	Repo, CI, multi-tenancy, auth, health checks, empty dashboard
1	Retailer Core	10 weeks	Live POS + inventory + receipts at 5 pilot shops
2	Compliance & Payments	5 weeks	eTIMS + M-Pesa + basic P&L + notifications
3	Purchasing & Network	8 weeks	Suppliers onboard, catalog, POs, RFQs
4	Ecosystem	8 weeks	Garages, job cards, marketplace, delivery
5	Intelligence & Scale	12 weeks	Forecasting, analytics, financing partners, white-label
Total: ~46 weeks (≈11 months) to full platform. Buffer to 14 months.

Each phase ends with a production release to real tenants, not a demo.

6. Phase details
Phase 0 — Foundation (3 weeks)
Goal: A deployable, empty, multi-tenant skeleton with real infrastructure.

Workstreams

Area	Deliverable
Repo	my_motii/ monorepo committed, .gitignore, .editorconfig, Makefile
Backend base	Django project, shared/ package installed editable, FastAPI bootstrapped with django.setup()
Tenancy	tenants app, TenantAwareManager, RLS policies, middleware
Auth	accounts app, JWT issuance in FastAPI, session model, 2FA skeleton
Infra	docker-compose with Postgres 16, Redis 7, nginx, backend, worker, beat
CI	GitHub Actions: lint, test, build on every PR
Observability	Structured logging + correlation ID, basic metrics endpoint, Sentry wired
Docs	ADRs 0001–0008, architecture overview, API conventions
Exit criteria

docker compose up produces a working stack

A user can register, log in, create a tenant, and see an empty dashboard

All E2E tests green in CI

One ADR per major decision

Risks

RLS misconfiguration → mitigate with row-level tests in CI

Django/FastAPI boundary drift → mitigate with ADR + code review rule

Phase 1 — Retailer Core (10 weeks)
Goal: Five pilot shops running their daily operations entirely on my_motii.

Workstreams

Area	Deliverable
Catalog	Products, categories, brands, UoM, barcodes, images
Fitment	Vehicle DB seed (top 200 Kenyan models), fitment links, OEM cross-reference
Inventory	Ledger, balances, reservations, stocktakes, transfers, reorder rules
POS	Register, cash session, checkout, end-of-day reconciliation
Documents	Invoice, receipt, quote, delivery note, credit note, gapless numbering
Printing	ESC/POS over WebUSB/Bluetooth, A4 PDF fallback
Customers	CRM, credit limit, credit balance, groups
Expenses	Categories, recurring, attachments, approvals
Reports	Daily sales, stock on hand, low stock, profit per part
Offline	Local IndexedDB, outbox queue, sync endpoint, conflict rules
Audit	Every mutation logged with before/after
Exit criteria

5 shops processing ≥200 real transactions/day combined for 14 consecutive days

Offline mode survives 8 hours disconnected with zero data loss

Receipts print on 3 certified thermal printer models

Stock accuracy ≥ 99.5% vs. physical count after a stocktake cycle

Support tickets ≤ 3 per shop per week

Risks

Offline sync conflicts → mitigate with append-only ledger + idempotency keys

Printer fragmentation → certify a small hardware list, publish compatibility matrix

Data import pain → build CSV/Excel importer with column mapping in week 1

Team focus: all backend, all frontend, QA heavily involved from week 2.

Phase 2 — Compliance & Payments (5 weeks)
Goal: Every transaction is KRA-compliant and every payment is reconciled.

Workstreams

Area	Deliverable
eTIMS	Client wrapper, transmission queue, retries, reconciliation, failure dashboard
M-Pesa	Daraja STK push, C2B, B2C, callbacks, matcher, auto-reconciliation
Payments	Payment methods, allocation across documents, refunds
Accounting	Chart of accounts, JE posting from events, cashbook, P&L, VAT report
Notifications	In-app, SMS, email, WhatsApp via template engine
Billing	SaaS subscription plans, invoicing, payment collection
Exit criteria

Every invoice generates a valid eTIMS submission within 60 seconds online, ≤5 minutes offline

Every M-Pesa transaction auto-matches to a sale or is flagged within 2 minutes

P&L for a test shop matches manual calculation to the shilling

Billing collected from 50 paying retailers

Risks

KRA API changes → isolate behind etims/clients/, monitor errors daily

M-Pesa callback reliability → always reconcile via Transaction Status as fallback

VAT edge cases → build an accountant-reviewed test suite

Phase 3 — Purchasing & Network (8 weeks)
Goal: Retailers order from suppliers inside the product; suppliers onboard as paying tenants.

Workstreams

Area	Deliverable
Suppliers	Supplier tenant type, catalogs, price lists, retailer-specific pricing
Connections	Retailer↔supplier link, visibility rules, consent
Purchasing	PO, GRN, supplier invoice, backorders, payment terms
RFQ	Multi-supplier RFQ, quote comparison, award
Supplier console	Full supplier SPA (orders, catalog, analytics, reps)
Alerts	Low-stock alerts to opted-in suppliers, demand aggregation
Delivery	Delivery orders, driver assignment, POD (signature + photo)
Exit criteria

40 suppliers onboarded with published catalogs

500 POs placed through the platform per month

Suppliers report time-to-quote improvement of ≥30%

Zero privacy violations on retailer data (verified by audit)

Risks

Supplier resistance → onboard first 10 manually, white-glove

Trust concerns → default to "network-only" visibility, opt-in for anything more

Data leakage → aggregated analytics only, contractually documented

Phase 4 — Ecosystem (8 weeks)
Goal: Garages and mechanics plug in; marketplace goes live with commissions.

Workstreams

Area	Deliverable
Garages	Garage tenant type, job cards, parts reservation, labor, billing
Mechanics	Mechanic accounts, specializations, vehicle service history
Marketplace	Listings, orders, delivery, commission engine
Reservation	Cross-tenant parts reservation (garage → retailer)
Delivery	Marketplace delivery, tracking, disputes
Exit criteria

100 garages using job cards monthly

Marketplace GMV ≥ KES 20M/month

Commission collection automated and reconciled

Cross-tenant reservation conflicts handled correctly (test suite proves it)

Risks

Garage adoption slower than expected → keep job cards optional, sell separately

Marketplace fraud → escrow via supplier balance, disputes workflow

Phase 5 — Intelligence & Scale (12 weeks)
Goal: Turn data into decisions and revenue.

Workstreams

Area	Deliverable
Analytics	Pre-aggregated daily metrics, cohort analysis, branch comparison
Forecasting	Demand forecast, reorder recommendation, dead stock identification
Auto-reorder	Rule-based, then forecast-based, one-click PO
Financing	Partner integrations (working capital, invoice factoring), referral fees
Data products	Anonymized industry reports for manufacturers
White-label	Association edition, custom domain, custom branding
Scale hardening	Horizontal scaling, read replicas, sharding strategy documented
Exit criteria

Forecast accuracy MAPE ≤ 25% on fast-moving SKUs

Auto-reorder approves ≥1,000 POs/month

Two financing partners live with signed referral agreements

Platform handles 10M API calls/day in load test

Risks

Regulatory exposure on financing → never hold capital, partner only

Data privacy → strict aggregation rules, DPO appointed, DPIA done

7. Team structure and responsibilities
7.1 Core team (Year 1)
Role	Count	Responsibilities
Founder / CTO	1	Product, architecture, key integrations, supplier relationships
Tech Lead	1	Backend review, ADRs, performance, mentoring
Backend Engineer (Django)	2	Domain apps, models, services, migrations
Backend Engineer (FastAPI)	1	API edge, sync, webhooks, integrations
Frontend Engineer (Retailer)	1	Retailer SPA, POS, offline
Frontend Engineer (Supplier + Admin)	1	Supplier console, platform admin
Desktop Engineer (Tauri)	1	POS desktop, printing, offline
QA Engineer	1	Test strategy, E2E, release verification
Product Designer	1	Design system, flows, usability
DevOps / SRE	1	Infra, CI/CD, observability, on-call
Support Lead	1	Onboarding, training, tickets, feedback loop
Total: 12 people.

7.2 Ownership matrix (RACI)
Area	Owner	Reviewer	Informed
Architecture	CTO	Tech Lead	All
Django domain	Tech Lead	Backend	—
FastAPI edge	Backend (FastAPI)	Tech Lead	—
Frontend	Frontend Lead	Designer	—
Offline sync	Backend (FastAPI) + Frontend	Tech Lead	CTO
eTIMS	Backend (Django)	CTO	—
M-Pesa	Backend (FastAPI)	CTO	—
Infrastructure	DevOps	CTO	All
Releases	QA	Tech Lead	All
Support escalation	Support Lead	Tech Lead	CTO
8. Engineering standards
8.1 Code
Python: Ruff + MyPy strict + Black-compatible formatting

TypeScript: ESLint + Prettier + tsc --noEmit in CI

Every PR requires: passing CI, ≥1 review, ADR if architectural, tests

No direct pushes to main

Trunk-based development with short-lived branches

8.2 Testing
Layer	Coverage target	Tools
Unit	80% domain services	pytest, vitest
Integration	100% of critical paths	pytest-django, httpx
E2E	Every release scenario	Playwright
Offline	Sync scenarios	pytest + simulated devices
Compliance	eTIMS, VAT, numbering	dedicated suite
Load	Monthly	Locust / k6
Critical path test (must always pass):

text
Retailer creates sale →
  inventory decreases →
  stock movement appended →
  payment recorded →
  accounting posted →
  receipt generated →
  eTIMS queued →
  analytics updated →
  notification triggered
8.3 Deployment
Blue/green or rolling deployments

Every deploy: migration check, smoke test, rollback plan

Feature flags for anything user-visible

Rollback within 5 minutes always possible

8.4 Documentation
Every Django app has a README.md explaining what it owns

Every ADR is a file, not a wiki page

API documented via OpenAPI, generated, versioned

Runbooks for: eTIMS failure, M-Pesa failure, sync backlog, DB failover, queue overflow

9. Data, compliance, and legal
9.1 Data protection (Kenya DPA 2019)
DPO appointed before Phase 1 goes live

DPIA completed for: analytics, supplier visibility, financing referrals

Data subject rights: export, deletion, correction — supported in product

Data residency: primary DB in Kenya or with Kenya-region hosting

Sub-processors listed publicly (AWS/cloud, SMS, WhatsApp, eTIMS integrator)

9.2 KRA / eTIMS
Integrate via KRA-approved middleware (never hard-code direct assumptions)

Isolated etims/ app; eTIMS specs can change without touching domain

Offline invoice queue with compliant transmission when connectivity returns

Full audit trail of submissions, responses, failures, retries

9.3 Financial
Never hold customer money — partner with a regulated PSP for any flow-through

Never lend — partner with banks/SACCOs; we refer, they underwrite

Escrow logic only for marketplace settlement, held at regulated PSP

9.4 Contracts needed
Retailer SaaS terms (per-tenant, per-branch)

Supplier network agreement (data visibility, consent, marketplace terms)

DPA between my_motii and each tenant (both directions)

Financing referral agreement (per partner)

eTIMS integrator agreement

Payment processor agreement

10. Monetization and pricing
10.1 Revenue streams (target mix by Year 3)
Stream	Year 1	Year 2	Year 3
Retailer SaaS	70%	45%	30%
Supplier SaaS	10%	20%	18%
Marketplace commission	0%	15%	20%
Payments facilitation	10%	8%	6%
Add-ons (eTIMS, SMS, analytics)	10%	7%	6%
Financing referral	0%	3%	10%
Data products	0%	2%	6%
Hardware / onboarding	0%	0%	4%
10.2 Retailer pricing
Plan	Price (KES/month)	Includes
Starter	1,500	1 branch, 2 users, POS, inventory, receipts
Business	5,000	+ branches, eTIMS, M-Pesa, credit mgmt, reports
Professional	12,000	+ warehouse, advanced analytics, API
Enterprise	Custom	+ isolated DB, SLA, dedicated support
10.3 Supplier pricing
Plan	Price (KES/month)	Includes
Free	0	Catalog listing, 5 orders/month
Growth	15,000	Unlimited orders, catalog sync, demand analytics
Pro	40,000	+ sales reps, territories, API, sponsored listings
Enterprise	Custom	+ dedicated account, custom integrations
10.4 Add-ons
eTIMS: KES 1,000/month

SMS bundles: from KES 500

WhatsApp: usage-based

Additional branches: KES 1,500 each

Additional users: KES 300 each

API access: KES 10,000/month

10.5 Marketplace
2% commission on B2B orders (supplier-paid, invoiced monthly)

Sponsored listings: KES 5,000–50,000/month per slot

Priority RFQ routing: included in Pro

10.6 Unit economics target
Metric	Target
Retailer CAC	≤ KES 8,000
Retailer LTV	≥ KES 90,000
Retailer payback	≤ 3 months
Retailer gross margin	≥ 78%
Logo retention (annual)	≥ 92%
Net revenue retention	≥ 115%
11. Go-to-market
11.1 Phase 1 GTM — Retailer acquisition
Direct sales in Nairobi CBD, Industrial Area, Kirinyaga Road, Mlolongo

Referral loop: 1 month free for each referred shop

Association partnerships: auto-parts dealer associations for bulk onboarding

Onboarding bundle: device + printer + setup for KES 25,000

11.2 Phase 3 GTM — Supplier acquisition
White-glove onboarding for first 20 suppliers

Sales rep tools as the wedge (they get a phone app)

Data as value: "you'll see demand before your competitors"

Buying group partnerships

11.3 Phase 4–5 GTM — Ecosystem
Garages via mechanics associations

Financing partners via bank partnerships

Data products to manufacturers and importers

11.4 Support model
WhatsApp-first support (this is how Kenyan SMBs communicate)

In-app chat

1-hour response SLA on Business and above

Weekly group training calls per region

Video library in English and Swahili

12. Risk register
#	Risk	Likelihood	Impact	Mitigation
1	Offline sync data loss	Medium	Critical	Append-only ledger, idempotency, extensive test suite, fallback manual entry
2	KRA eTIMS API change	High	High	Isolate module, use approved integrator, monitor daily, budget for rework
3	M-Pesa downtime	Medium	High	Cash + manual fallback, C2B + Transaction Status reconciliation
4	Retailer churn in first 90 days	High	High	Onboarding program, weekly check-ins for first month, NPS at 30/60/90
5	Supplier resistance	High	Medium	Free tier, manual onboarding, honest data-privacy stance
6	Data leak across tenants	Low	Critical	RLS + automated cross-tenant tests + periodic audits
7	Key engineer departure	Medium	High	No bus-factor-1 systems, code review, documentation
8	Pricing under-monetizes	Medium	Medium	Annual price review, usage-based add-ons
9	Financing partner fails	Medium	Low	Multiple partners, never principal
10	Hardware incompatibility	High	Medium	Certified device list, in-app device checker
11	Payment fraud on marketplace	Medium	High	Escrow via PSP, KYC on suppliers, dispute SLA
12	Regulatory change (DPA, tax)	Medium	High	Legal counsel retainer, quarterly compliance review
13	Cloud cost overrun	Medium	Medium	Cost dashboards, budgets, alerts at 80%
14	Support overload	High	Medium	Self-serve training, community, tiered support
15	Feature creep from customers	High	Medium	Roadmap governance, "not yet" library, feedback portal
Escalation: any Critical-impact risk with >Medium likelihood requires a written mitigation plan within 7 days.

13. Success metrics
13.1 Product metrics
Metric	Phase 1 target	Year 1 target
DAU / tenant	≥3 users	≥5 users
Transactions per shop per day	≥200	≥400
Offline sync success rate	≥99.9%	≥99.95%
Receipt print success	≥98%	≥99.5%
Stock accuracy after stocktake	≥99%	≥99.5%
eTIMS submission success (online)	≥99%	≥99.8%
13.2 Business metrics
Metric	Year 1	Year 2	Year 3
Paying retailers	500	3,000	8,000
Active suppliers	40	250	700
ARR (KES)	12M	90M	320M
Gross margin	70%	75%	80%
Net revenue retention	105%	115%	120%
Churn (annual logo)	15%	10%	8%
CAC payback (months)	4	3	2
13.3 Quality metrics
Metric	Target
Uptime (business hours)	≥99.9%
P95 API latency	≤300ms
P95 sync endpoint latency	≤500ms
Error rate	≤0.1% of requests
Support first response	≤1 hour
Critical bug MTTR	≤4 hours
Deploy frequency	≥2 per week
14. Governance and decision log
14.1 Rituals
Ritual	Cadence	Owner	Output
Standup	Daily	Tech Lead	Blockers cleared
Sprint planning	Biweekly	CTO	Sprint scope
Sprint review	Biweekly	CTO	Demo + metrics
Retro	Biweekly	Tech Lead	Process improvements
Architecture review	As needed	CTO	ADR
Release review	Per release	QA	Go/no-go
Business review	Monthly	Founder	KPI review + adjustments
Security review	Quarterly	CTO	Audit + remediation plan
Compliance review	Quarterly	DPO	DPIA updates, legal changes
14.2 Decision rights
Decision	Decider	Consulted	Informed
Architecture	CTO	Tech Lead	Team
New feature (scope)	Founder	CTO	Team
New vendor / integration	CTO	Founder	Team
Pricing change	Founder	CTO	Team
Hire	Founder	CTO	Team
Production incident	On-call	Tech Lead	CTO
Security incident	CTO	DPO, Founder	Regulator if required
Compliance breach	DPO	CTO, Founder	Regulator
14.3 ADR process
Every architectural decision has a numbered ADR in docs/architecture/adr/

ADR format: Context, Decision, Consequences, Status, Date

ADRs are immutable once Accepted; changes create a new ADR that supersedes

14.4 Definition of done (per feature)
Code merged with passing CI

Unit + integration tests written

E2E test if user-facing

Documentation updated (README, API, user help)

Feature flag in place (if applicable)

Analytics event added

Reviewed by Tech Lead

14.5 Definition of shipped (per phase)
All phase deliverables complete

Exit criteria met and demonstrated

Rollback plan documented and tested

Support team trained

Marketing / GTM material ready

Post-launch monitoring in place for 30 days

15. Appendices
A. Glossary
Term	Meaning
Tenant	A SaaS customer account (retailer or supplier)
Organization	The legal business behind a tenant
Branch	Physical location of an organization
Stock movement	An atomic change to inventory (sale, purchase, adjustment)
Document	Any numbered business artifact (invoice, receipt, PO, credit note)
Sync batch	A set of offline operations transmitted together
Idempotency key	Unique key that ensures an operation is applied exactly once
RFQ	Request for Quotation
GRN	Goods Received Note
OEM	Original Equipment Manufacturer
eTIMS	Electronic Tax Invoice Management System (KRA)
B. Key integrations
Integration	Purpose	Fallback
KRA eTIMS	Tax invoice submission	Offline queue, retry
M-Pesa Daraja	Payments (STK, C2B, B2C)	Cash, manual reconciliation
WhatsApp Cloud	Customer comms, notifications	SMS, in-app
Africa's Talking	SMS	Twilio
Bank / card PSP	Card payments	Cash
S3-compatible storage	Files, PDFs, images	Local disk (dev)
Sentry	Error tracking	Logs
C. Phase timeline at a glance
text
Month  1  2  3  4  5  6  7  8  9 10 11 12 13 14
P0     ███
P1        ██████████
P2                    █████
P3                         ████████
P4                                  ████████
P5                                           ████████████
D. Reference documents
docs/architecture/overview.md — system architecture

docs/architecture/adr/ — all ADRs

docs/domain/ — domain notes per app

docs/tenancy/ — multitenancy model

docs/offline/ — sync protocol

docs/integrations/ — external integration specs

docs/ops/runbooks/ — operational runbooks

docs/product/roadmap.md — living roadmap

E. Change log
Version	Date	Change	Author
1.0	2026-09-21	Initial implementation plan	Founder / CTO
End of document.

This plan is a living document. Every phase exit triggers a review and, if needed, a version bump with an entry in Appendix E. Any deviation from Section 4 (Architecture Principles) requires an ADR before implementation begins.