import enum

class UserRole(str, enum.Enum):
    FOOD_DEPARTMENT = "FOOD_DEPARTMENT"
    PANCHAYAT_SAMITI = "PANCHAYAT_SAMITI"
    GRAM_PANCHAYAT = "GRAM_PANCHAYAT"
    FARMER = "FARMER"
    MAJOR_WAREHOUSE = "MAJOR_WAREHOUSE"
    MINOR_WAREHOUSE = "MINOR_WAREHOUSE"
    BULK_BUYER = "BULK_BUYER"
    ADMIN = "ADMIN"

ROLE_METADATA = {
    UserRole.FOOD_DEPARTMENT: {
        "title": "Food Department",
        "description": "State/Central authority overseeing statewide food grain planning, reserves, and policy allocation.",
        "tier_index": 1,
        "is_supply_chain_node": True,
        "requires_custom_id": False,
    },
    UserRole.PANCHAYAT_SAMITI: {
        "title": "Panchayat Samiti",
        "description": "Block-level administrative council aggregating cluster targets, block quota, and extension activities.",
        "tier_index": 2,
        "is_supply_chain_node": True,
        "requires_custom_id": False,
    },
    UserRole.GRAM_PANCHAYAT: {
        "title": "Gram Panchayat",
        "description": "Village-level local governing council coordinating directly with farmers and field verification.",
        "tier_index": 3,
        "is_supply_chain_node": True,
        "requires_custom_id": False,
    },
    UserRole.FARMER: {
        "title": "Farmer",
        "description": "Agricultural producer managing field plots, crop cycles, harvest reporting, and grain delivery.",
        "tier_index": 4,
        "is_supply_chain_node": True,
        "requires_custom_id": True,
        "id_prefix": "KS-FMR",
    },
    UserRole.MAJOR_WAREHOUSE: {
        "title": "Major Warehouse",
        "description": "Central / Regional Strategic Reserve Warehouse handling heavy storage and bulk lot allocations.",
        "tier_index": 5,
        "is_supply_chain_node": True,
        "requires_custom_id": False,
    },
    UserRole.MINOR_WAREHOUSE: {
        "title": "Minor Warehouse",
        "description": "Sub-district/block warehouse providing localized buffer capacity, rapid intake, and regional distribution.",
        "tier_index": 6,
        "is_supply_chain_node": True,
        "requires_custom_id": False,
    },
    UserRole.BULK_BUYER: {
        "title": "Bulk Buyer",
        "description": "Authorized commercial entity, processor, or institution procuring grains in bulk lots.",
        "tier_index": 7,
        "is_supply_chain_node": True,
        "requires_custom_id": True,
        "id_prefix": "KS-BYR",
    },
    UserRole.ADMIN: {
        "title": "System Administrator",
        "description": "Platform management, user provisioning, system health monitoring, and governance auditing.",
        "tier_index": 0,
        "is_supply_chain_node": False,
        "requires_custom_id": False,
    },
}

