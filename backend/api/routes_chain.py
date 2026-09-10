from fastapi import APIRouter
from backend.models.schemas import SupplyChainResponse, SupplyChainNode
from backend.models.enums import UserRole, ROLE_METADATA

router = APIRouter(prefix="/api/chain", tags=["Supply Chain Connectivity"])

SUPPLY_CHAIN_ORDER = [
    UserRole.FOOD_DEPARTMENT,
    UserRole.PANCHAYAT_SAMITI,
    UserRole.GRAM_PANCHAYAT,
    UserRole.FARMER,
    UserRole.MAJOR_WAREHOUSE,
    UserRole.MINOR_WAREHOUSE,
    UserRole.BULK_BUYER,
]

@router.get("/nodes", response_model=SupplyChainResponse)
def get_supply_chain_nodes():
    """
    Returns the connected 7-tier KrushiSetu supply chain structure:
    Food Department → Panchayat Samiti → Gram Panchayat → Farmer → Major Warehouse → Minor Warehouse → Bulk Buyer
    """
    nodes = []
    for idx, role_enum in enumerate(SUPPLY_CHAIN_ORDER, start=1):
        meta = ROLE_METADATA[role_enum]
        nodes.append(
            SupplyChainNode(
                tier=idx,
                role=role_enum,
                name=meta["title"],
                description=meta["description"],
                requires_custom_id=meta.get("requires_custom_id", False),
                id_format=f"{meta.get('id_prefix')}-XXXX" if meta.get("requires_custom_id") else None,
            )
        )

    return SupplyChainResponse(
        pipeline="Food Department → Panchayat Samiti → Gram Panchayat → Farmer → Major Warehouse → Minor Warehouse → Bulk Buyer",
        total_tiers=len(nodes),
        nodes=nodes,
    )

