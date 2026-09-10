# KRUSHISETU Platform Architecture

## 1. Vision & Purpose

**KrushiSetu (कृषीसेतू)** is an AI-driven agricultural planning, crop production, warehouse, logistics, and traceability platform designed to eliminate supply chain silos, optimize grain reserves, empower agricultural producers, and streamline bulk institutional commerce.

The platform unifies 7 operational tiers in a cohesive sequence:

```
Food Department
      │
      ▼
Panchayat Samiti
      │
      ▼
Gram Panchayat
      │
      ▼
   Farmer (KS-FMR-XXXX)
      │
      ▼
Major Warehouse
      │
      ▼
Minor Warehouse
      │
      ▼
 Bulk Buyer (KS-BYR-XXXX)
```

---

## 2. Core Principle: One Central AI/ML Engine

All telemetry, farmer harvest estimates, soil health data, warehouse stock levels, logistic bottlenecks, and buyer demand curves flow into **ONE CENTRAL AI/ML ENGINE**.

The engine operates continuously to:
1. Forecast statewide grain needs and recommend district crop allocations.
2. Direct village-level acreage quotas to prevent glut and scarcity.
3. Verify harvest grading through computer vision against national quality standards.
4. Dynamically route logistics between minor mandi transit godowns and strategic major silos.
5. Provide transparent market pricing and demand fulfillment for bulk buyers.

In Stage 1, the AI Engine singleton stub (`backend/ai/engine.py`) defines clean interface contracts and data pipelines so models can be plugged in seamlessly in subsequent stages without architectural rewrites.

---

## 3. The 8 Basic Roles

| # | Role Key | Title | Tier | ID Scheme | Scope & Responsibility |
|---|---|---|---|---|---|
| 1 | `FOOD_DEPARTMENT` | Food Department | 1 | Institutional | Statewide strategic food grain planning, buffer stocks, and allocation policies. |
| 2 | `PANCHAYAT_SAMITI` | Panchayat Samiti | 2 | Institutional | Block-level administrative council aggregating cluster targets and crop plans. |
| 3 | `GRAM_PANCHAYAT` | Gram Panchayat | 3 | Institutional | Village council coordinating directly with farmers, verifying land & crops. |
| 4 | `FARMER` | Farmer | 4 | `KS-FMR-XXXX` | Agricultural producer managing field plots, crop cycles, and grain intake. |
| 5 | `MAJOR_WAREHOUSE` | Major Warehouse | 5 | Institutional | Central/Regional Strategic Reserve Silo handling heavy storage (e.g. 50,000 MT). |
| 6 | `MINOR_WAREHOUSE` | Minor Warehouse | 6 | Institutional | Block/APMC transit godown providing local buffer capacity and intake. |
| 7 | `BULK_BUYER` | Bulk Buyer | 7 | `KS-BYR-XXXX` | Commercial entity, food processor, or exporter procuring grains in bulk lots. |
| 8 | `ADMIN` | System Administrator | 0 | Institutional | Platform maintenance, user management, and system health governance. |

> **Citizen Policy:** Citizens do NOT receive IDs and do not have an operational portal in this stage.

---

## 4. Technical Architecture

### Backend
- **Framework**: Python 3.14 + FastAPI
- **Security**: JWT (HS256) bearer tokens + bcrypt password hashing
- **ORM**: SQLAlchemy 2.0 (Declarative Base)
- **Database Engine**:
  - Development: SQLite (`/data/krushisetu.db`) with `check_same_thread=False`
  - Production: PostgreSQL ready via `DATABASE_URL` environment variable (`postgresql://user:password@host:port/dbname`)

### Frontend
- **Tech**: HTML5, CSS3, Vanilla JavaScript (zero heavy client dependencies)
- **Theme**: Clean Indian government agriculture aesthetic (Forest Green `#1b5e20`, Kisan Green `#2e7d32`, Amber `#f57f17`)
- **Responsiveness**: Fluid layout with responsive navigation, grid cards, and mobile sidebar support

---

## 5. Folder Structure Reference

```
KRUSHISETU/
├── backend/
│   ├── ai/
│   │   ├── __init__.py
│   │   └── engine.py               # Central AI/ML engine interface stub
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_auth.py          # /api/auth endpoints
│   │   ├── routes_chain.py         # /api/chain supply chain topology
│   │   └── routes_health.py        # /api/health endpoint
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py           # SQLAlchemy engine & session factory
│   │   └── init_db.py              # Table setup & initial role accounts seed
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py                # UserRole enum & metadata
│   │   ├── schemas.py              # Pydantic schemas
│   │   └── user.py                 # SQLAlchemy User model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Bcrypt & JWT logic
│   │   └── id_generator.py         # KS-FMR-XXXX and KS-BYR-XXXX generator
│   └── main.py                     # FastAPI application
├── frontend/
│   ├── assets/                     # SVG logo and icons
│   ├── css/
│   │   └── style.css               # Portal design system
│   ├── js/
│   │   ├── api.js                  # Central fetch wrapper
│   │   ├── auth.js                 # Auth form handlers
│   │   └── dashboard.js            # Role-aware dashboard shell
│   └── pages/
│       ├── index.html              # Landing portal
│       ├── login.html              # Unified login
│       ├── register.html           # Farmer/Buyer onboarding
│       └── dashboard.html          # Operational console
├── data/                           # Local SQLite storage
├── docs/
│   ├── ARCHITECTURE.md             # This document
│   └── API_SPEC.md                 # REST API reference
├── requirements.txt
└── run.py
```

