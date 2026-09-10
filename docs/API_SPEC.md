# KRUSHISETU - REST API Specification (Stage 1)

Base URL: `http://127.0.0.1:8000`  
OpenAPI Documentation: `http://127.0.0.1:8000/docs`

---

## 1. Health & Diagnostics

### `GET /api/health`
Checks backend responsiveness, database connectivity, and central AI engine status.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "project": "KrushiSetu",
  "version": "1.0.0",
  "database": "connected",
  "ai_engine_ready": true
}
```

---

## 2. Authentication & Roles

### `POST /api/auth/login`
Authenticates a user by username or email.

**Request Body**:
```json
{
  "username": "farmer_demo",
  "password": "Krushi@123"
}
```

**Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 5,
    "username": "farmer_demo",
    "email": "ramesh.patil@krushisetu.gov.in",
    "role": "FARMER",
    "role_title": "Farmer",
    "farmer_id": "KS-FMR-1001",
    "buyer_id": null,
    "full_name": "Ramesh Narayan Patil",
    "phone": null,
    "jurisdiction_or_location": "Plot No. 42, Shirsuphal Village",
    "is_active": true
  }
}
```

---

### `GET /api/auth/me`
Retrieves the profile of the currently logged-in user.

**Headers**:
`Authorization: Bearer <access_token>`

**Response `200 OK`**:
```json
{
  "id": 5,
  "username": "farmer_demo",
  "email": "ramesh.patil@krushisetu.gov.in",
  "role": "FARMER",
  "role_title": "Farmer",
  "farmer_id": "KS-FMR-1001",
  "buyer_id": null,
  "full_name": "Ramesh Narayan Patil",
  "phone": null,
  "jurisdiction_or_location": "Plot No. 42, Shirsuphal Village",
  "is_active": true
}
```

---

### `POST /api/auth/register`
Self-registration for Farmers (`FARMER`) and Bulk Buyers (`BULK_BUYER`).  
Automatically assigns `KS-FMR-XXXX` or `KS-BYR-XXXX`.

**Request Body**:
```json
{
  "username": "suresh_farmer",
  "email": "suresh@example.com",
  "password": "SecretPassword123",
  "role": "FARMER",
  "full_name": "Suresh Kisan Shinde",
  "phone": "+91 98220 12345",
  "jurisdiction_or_location": "Shirsuphal Village, Baramati"
}
```

**Response `200 OK`**:
```json
{
  "id": 9,
  "username": "suresh_farmer",
  "email": "suresh@example.com",
  "role": "FARMER",
  "role_title": "Farmer",
  "farmer_id": "KS-FMR-1002",
  "buyer_id": null,
  "full_name": "Suresh Kisan Shinde",
  "phone": "+91 98220 12345",
  "jurisdiction_or_location": "Shirsuphal Village, Baramati",
  "is_active": true
}
```

---

### `GET /api/auth/roles`
Returns all 8 supported roles, their hierarchy, and identifier requirements.

**Response `200 OK`**:
```json
[
  {
    "key": "ADMIN",
    "title": "System Administrator",
    "description": "Platform management...",
    "tier_index": 0,
    "is_supply_chain_node": false,
    "requires_custom_id": false,
    "id_prefix": null
  },
  {
    "key": "FOOD_DEPARTMENT",
    "title": "Food Department",
    "description": "State/Central authority...",
    "tier_index": 1,
    "is_supply_chain_node": true,
    "requires_custom_id": false,
    "id_prefix": null
  },
  ...
]
```

---

## 3. Supply Chain Connectivity

### `GET /api/chain/nodes`
Returns the 7 sequential supply chain nodes in KrushiSetu.

**Response `200 OK`**:
```json
{
  "pipeline": "Food Department → Panchayat Samiti → Gram Panchayat → Farmer → Major Warehouse → Minor Warehouse → Bulk Buyer",
  "total_tiers": 7,
  "nodes": [
    {"tier": 1, "role": "FOOD_DEPARTMENT", "name": "Food Department", "requires_custom_id": false},
    {"tier": 2, "role": "PANCHAYAT_SAMITI", "name": "Panchayat Samiti", "requires_custom_id": false},
    {"tier": 3, "role": "GRAM_PANCHAYAT", "name": "Gram Panchayat", "requires_custom_id": false},
    {"tier": 4, "role": "FARMER", "name": "Farmer", "requires_custom_id": true, "id_format": "KS-FMR-XXXX"},
    {"tier": 5, "role": "MAJOR_WAREHOUSE", "name": "Major Warehouse", "requires_custom_id": false},
    {"tier": 6, "role": "MINOR_WAREHOUSE", "name": "Minor Warehouse", "requires_custom_id": false},
    {"tier": 7, "role": "BULK_BUYER", "name": "Bulk Buyer", "requires_custom_id": true, "id_format": "KS-BYR-XXXX"}
  ]
}
```

